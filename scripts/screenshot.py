import sys
import io
import ctypes
import os
import struct
import zlib
from ctypes import (
    byref, memset, pointer, sizeof, windll,
    c_void_p as LPRECT,
    c_void_p as LPVOID,
    create_string_buffer,
    Structure,
    POINTER,
    WINFUNCTYPE,
)
from ctypes.wintypes import (
    BOOL,
    DOUBLE,
    DWORD,
    HBITMAP,
    HDC,
    HGDIOBJ,
    HWND,
    INT,
    LONG,
    LPARAM,
    RECT,
    UINT,
    WORD,
    LPVOID
)

CAPTUREBLT = 0x40000000
DIB_RGB_COLORS = 0
SRCCOPY = 0x00CC0020
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

class BITMAPINFOHEADER(Structure):
    """ Information about the dimensions and color format of a DIB. """

    _fields_ = [
        ("biSize", DWORD),
        ("biWidth", LONG),
        ("biHeight", LONG),
        ("biPlanes", WORD),
        ("biBitCount", WORD),
        ("biCompression", DWORD),
        ("biSizeImage", DWORD),
        ("biXPelsPerMeter", LONG),
        ("biYPelsPerMeter", LONG),
        ("biClrUsed", DWORD),
        ("biClrImportant", DWORD),
    ]


class BITMAPINFO(Structure):
    """
    Structure that defines the dimensions and color information for a DIB.
    """

    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", DWORD * 3)]

MONITORNUMPROC = WINFUNCTYPE(INT, DWORD, DWORD, POINTER(RECT), DOUBLE)

# Methods
GetSystemMetrics = windll.user32.GetSystemMetrics
windll.user32.GetSystemMetrics.argtypes = [INT]
windll.user32.GetSystemMetrics.restype = INT

GetWindowDC = windll.user32.GetWindowDC
windll.user32.GetWindowDC.argtypes = [HWND]
windll.user32.GetWindowDC.restype = HDC

CreateCompatibleDC = windll.gdi32.CreateCompatibleDC
windll.gdi32.CreateCompatibleDC.argtypes = [HDC]
windll.gdi32.CreateCompatibleDC.restype = HDC

CreateCompatibleBitmap = windll.gdi32.CreateCompatibleBitmap
windll.gdi32.CreateCompatibleBitmap.argtypes = [HDC, INT, INT]
windll.gdi32.CreateCompatibleBitmap.restype = HBITMAP

SelectObject = windll.gdi32.SelectObject
windll.gdi32.SelectObject.argtypes = [HDC, HGDIOBJ]
windll.gdi32.SelectObject.restype = HGDIOBJ

BitBlt = windll.gdi32.BitBlt
windll.gdi32.BitBlt.argtypes = [HDC, INT, INT, INT, INT, HDC, INT, INT, DWORD]
windll.gdi32.BitBlt.restype =  BOOL

GetDIBits = windll.gdi32.GetDIBits
windll.gdi32.GetDIBits.argtypes = [HDC, HBITMAP, UINT, UINT, LPVOID,
    POINTER(BITMAPINFO), UINT]
windll.gdi32.GetDIBits.restype = INT

DeleteObject = windll.gdi32.DeleteObject
windll.gdi32.DeleteObject.argtypes = [HGDIOBJ]
windll.gdi32.DeleteObject.restype = BOOL

def get_monitor_values():
    left = GetSystemMetrics(SM_XVIRTUALSCREEN)
    right = GetSystemMetrics(SM_CXVIRTUALSCREEN)
    top = GetSystemMetrics(SM_YVIRTUALSCREEN)
    bottom = GetSystemMetrics(SM_CYVIRTUALSCREEN)
    width = right - left
    height = bottom - top
    return left, right, top, bottom, width, height

def screenshot():
    srcdc = memdc = None
    left, right, top, bottom, width, height = get_monitor_values()
    srcdc = GetWindowDC(None)
    if srcdc is None:
        raise Exception("srcdc = GetWindowDC(None) has failed")

    memdc = CreateCompatibleDC(srcdc)
    if memdc is None:
        raise Exception("memdc = CreateCompatibleDC(srcdc) has failed")

    bmp = CreateCompatibleBitmap(srcdc, width, height)
    try:
        SelectObject(memdc, bmp)
        BitBlt(memdc, 0, 0, width, height, srcdc, left, top, SRCCOPY | CAPTUREBLT)
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height
        bmi.bmiHeader.biBitCount = 24
        bmi.bmiHeader.biPlanes = 1
        buffer_len = height * ((width * 3 + 3) & -4)
        pixels = create_string_buffer(buffer_len)
        bits = GetDIBits(memdc, bmp, 0, height, byref(pixels),
            pointer(bmi), DIB_RGB_COLORS)
    finally:
        DeleteObject(srcdc)
        DeleteObject(memdc)
        DeleteObject(bmp)

    if bits != height or len(pixels.raw) != buffer_len:
        raise ValueError('MSSWindows: GetDIBits() failed.')
    if bits is not None:
        print("GetDIBits succeded, lines scanned: ", bits)
    return pixels.raw, width, height

def to_png(data, size, level=6, output=None):

    pack = struct.pack
    crc32 = zlib.crc32

    width, height = size
    line = width * 3
    png_filter = pack(">B", 0)
    scanlines = b"".join(
        [png_filter + data[y * line : y * line + line] for y in range(height)]
    )

    magic = pack(">8B", 137, 80, 78, 71, 13, 10, 26, 10)

    # Header: size, marker, data, CRC32
    ihdr = [b"", b"IHDR", b"", b""]
    ihdr[2] = pack(">2I5B", width, height, 8, 2, 0, 0, 0)
    ihdr[3] = pack(">I", crc32(b"".join(ihdr[1:3])) & 0xFFFFFFFF)
    ihdr[0] = pack(">I", len(ihdr[2]))

    # Data: size, marker, data, CRC32
    idat = [b"", b"IDAT", zlib.compress(scanlines, level), b""]
    idat[3] = pack(">I", crc32(b"".join(idat[1:3])) & 0xFFFFFFFF)
    idat[0] = pack(">I", len(idat[2]))

    # Footer: size, marker, None, CRC32
    iend = [b"", b"IEND", b"", b""]
    iend[3] = pack(">I", crc32(iend[1]) & 0xFFFFFFFF)
    iend[0] = pack(">I", len(iend[2]))

    if not output:
        # Returns raw bytes of the whole PNG data
        return magic + b"".join(ihdr + idat + iend)

    with open(output, "wb") as fileh:
        fileh.write(magic)
        fileh.write(b"".join(ihdr))
        fileh.write(b"".join(idat))
        fileh.write(b"".join(iend))

        # Force write of file to disk
        fileh.flush()
        os.fsync(fileh.fileno())

    return None

def connect_dots():
    raw_data, width, height = screenshot()
    to_png(raw_data, (width, height), output="D:\\Personal\\Source\\local\\test.png")

connect_dots()