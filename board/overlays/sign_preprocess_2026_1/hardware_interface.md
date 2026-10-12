# Image preprocessing hardware interface

## Overlay

Use board/overlays/sign_preprocess_2026_1/sign_preprocess_2026_1.bit
and the same-name .hwh. Both were copied from the 2026.1 system build.
This pairing has not yet been loaded on a physical board.

## HLS image protocol

Fixed image: 360 x 360 = 129600 pixels, row-major order.
HLS input: 24 bits, R in [23:16], G in [15:8], B in [7:0].
OpenCV BGR must be converted to RGB before packing.
HLS output: 8 bits per pixel, either 0 or 255.
USER is 1 only on the first output pixel; TLAST is 1 only on the
last pixel of the frame, not at each row end.
Morphology is a zero-padded 3x3 majority filter (at least 5 foreground
neighbors), not erosion/dilation opening or closing.

## AXI-Lite offsets

| Register | Offset | Default |
| --- | --- | --- |
| AP_CTRL | 0x00 | start bit 0, done bit 1 |
| y_min | 0x10 | 45 |
| y_max | 0x18 | 225 |
| cr_min | 0x20 | 135 |
| cr_max | 0x28 | 190 |
| cb_min | 0x30 | 80 |
| cb_max | 0x38 | 145 |
| enable_morphology | 0x40 | 0 or 1 |

Offsets come from the exported ximage_preprocess_hw.h.
Use the HWH/register_map for the actual IP instance and base address.

## DMA contract requiring board confirmation

The input contains 388800 useful bytes and output 129600 useful bytes.
These are HLS payload lengths, not proof of the DMA buffer layout.
The 32-to-24 converter configuration determines whether memory is a
packed byte sequence or one padded word per pixel. Do not assume that
129600 uint32 RGB words equal the packed input stream.
Confirm converter TKEEP/byte packing, DMA length capacity, and byte order
from HWH and a fixed-vector board transaction before using a camera.
Arm S2MM first, configure/start the HLS IP, then send MM2S; use timeout,
cache handling and recovery from board/dma_transfer.py.

## Offline verification

One existing real image was checked in C simulation with morphology 0
and 1: 129600 pixels per mode, 0 mismatches, USER/TLAST checks passed.
This does not verify RTL timing, DMA packing or physical board behavior.
