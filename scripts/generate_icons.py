"""Generate iOS / PWA app icons from Nagisa's square master icon.

Pure standard-library implementation: decodes an RGB 8-bit PNG,
area-averages it down to the requested sizes, and re-encodes each icon
as a filtered PNG. No third-party dependencies required.
"""

import math
import struct
import zlib
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "frontend" / "assets"
SOURCE = OUTPUT_DIR / "nagisa-app-icon-1024.png"
OUTPUT_PREFIX = "nagisa-app-icon"

# iOS "Add to Home Screen" icons + PWA manifest icons.
SIZES = (180, 192, 512, 1024)


class PngError(RuntimeError):
    pass


def read_chunks(data: bytes):
    """Yield (type, payload) pairs from a PNG byte stream."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise PngError("not a PNG file")

    pos = 8
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        chunk_type = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        yield chunk_type, payload
        pos += 12 + length


def decode_png(path: Path):
    raw = path.read_bytes()
    ihdr = None
    idat = bytearray()

    for chunk_type, payload in read_chunks(raw):
        if chunk_type == b"IHDR":
            ihdr = payload
        elif chunk_type == b"IDAT":
            idat.extend(payload)
        elif chunk_type == b"IEND":
            break

    if ihdr is None:
        raise PngError("missing IHDR")

    width, height, bit_depth, color_type, compression, filter_method, interlace = (
        struct.unpack(">IIBBBBB", ihdr)
    )
    if bit_depth != 8:
        raise PngError(f"unsupported bit depth: {bit_depth}")
    if color_type != 2:
        raise PngError(
            f"unsupported color type: {color_type} "
            "(only RGB 8-bit supported)"
        )
    if compression != 0 or filter_method != 0:
        raise PngError("unsupported compression/filter method")
    if interlace != 0:
        raise PngError("interlaced PNGs are not supported")

    channels = 3
    stride = width * channels
    scanline_size = stride + 1

    decompressed = zlib.decompress(bytes(idat))
    expected = scanline_size * height
    if len(decompressed) != expected:
        raise PngError(
            f"unexpected decoded size: got {len(decompressed)}, "
            f"expected {expected}"
        )

    pixels = bytearray(stride * height)

    def paeth(a, b, c):
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)
        if pa <= pb and pa <= pc:
            return a
        if pb <= pc:
            return b
        return c

    for y in range(height):
        row_in = y * scanline_size
        row_out = y * stride
        filter_type = decompressed[row_in]

        for x in range(stride):
            raw_byte = decompressed[row_in + 1 + x]
            left = pixels[row_out + x - channels] if x >= channels else 0
            up = pixels[row_out + x - stride] if y > 0 else 0
            up_left = (
                pixels[row_out + x - stride - channels]
                if (y > 0 and x >= channels)
                else 0
            )

            if filter_type == 0:
                recon = raw_byte
            elif filter_type == 1:
                recon = raw_byte + left
            elif filter_type == 2:
                recon = raw_byte + up
            elif filter_type == 3:
                recon = raw_byte + ((left + up) >> 1)
            elif filter_type == 4:
                recon = raw_byte + paeth(left, up, up_left)
            else:
                raise PngError(f"unknown filter type: {filter_type}")

            pixels[row_out + x] = recon & 0xFF

    return width, height, pixels


def resize_area(width, height, pixels, dst_size):
    """Downscale using area averaging (box filter)."""
    dst = dst_size
    out = bytearray(dst * dst * 3)
    scale = width / dst

    for dy in range(dst):
        sy0 = dy * scale
        sy1 = (dy + 1) * scale
        y_start = int(sy0)
        y_end = min(int(math.ceil(sy1)), height)

        for dx in range(dst):
            sx0 = dx * scale
            sx1 = (dx + 1) * scale
            x_start = int(sx0)
            x_end = min(int(math.ceil(sx1)), width)

            red_total = 0
            green_total = 0
            blue_total = 0
            for sy in range(y_start, y_end):
                row = sy * (width * 3)
                for sx in range(x_start, x_end):
                    i = row + sx * 3
                    red_total += pixels[i]
                    green_total += pixels[i + 1]
                    blue_total += pixels[i + 2]

            count = (y_end - y_start) * (x_end - x_start)
            idx = (dy * dst + dx) * 3
            out[idx] = red_total // count
            out[idx + 1] = green_total // count
            out[idx + 2] = blue_total // count

    return out


def encode_png(size, pixels):
    """Encode an RGB 8-bit image as a non-interlaced PNG (filter 0)."""
    def chunk(chunk_type, payload):
        chunk_type_bytes = chunk_type.encode("ascii")
        length = struct.pack(">I", len(payload))
        crc = zlib.crc32(chunk_type_bytes + payload) & 0xFFFFFFFF
        return (
            length
            + chunk_type_bytes
            + payload
            + struct.pack(">I", crc)
        )

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    stride = size * 3
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter: None
        raw.extend(pixels[y * stride:(y + 1) * stride])

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk("IHDR", ihdr)
        + chunk("IDAT", zlib.compress(bytes(raw), 9))
        + chunk("IEND", b"")
    )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Source: {SOURCE}")
    width, height, pixels = decode_png(SOURCE)
    print(f"Decoded {width}x{height} RGB image")

    for size in SIZES:
        if size > width:
            print(f"  skipping {size} (larger than source)")
            continue

        resized = resize_area(width, height, pixels, size)
        png = encode_png(size, resized)
        out_path = OUTPUT_DIR / f"{OUTPUT_PREFIX}-{size}.png"
        out_path.write_bytes(png)
        print(f"  wrote {out_path.name} ({size}x{size}, {len(png)} bytes)")


if __name__ == "__main__":
    main()
