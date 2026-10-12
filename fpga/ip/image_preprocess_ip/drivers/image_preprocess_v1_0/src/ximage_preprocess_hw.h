// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
// control
// 0x00 : Control signals
//        bit 0  - ap_start (Read/Write/COH)
//        bit 1  - ap_done (Read/COR)
//        bit 2  - ap_idle (Read)
//        bit 3  - ap_ready (Read/COR)
//        bit 7  - auto_restart (Read/Write)
//        bit 9  - interrupt (Read)
//        others - reserved
// 0x04 : Global Interrupt Enable Register
//        bit 0  - Global Interrupt Enable (Read/Write)
//        others - reserved
// 0x08 : IP Interrupt Enable Register (Read/Write)
//        bit 0 - enable ap_done interrupt (Read/Write)
//        bit 1 - enable ap_ready interrupt (Read/Write)
//        others - reserved
// 0x0c : IP Interrupt Status Register (Read/TOW)
//        bit 0 - ap_done (Read/TOW)
//        bit 1 - ap_ready (Read/TOW)
//        others - reserved
// 0x10 : Data signal of y_min
//        bit 7~0 - y_min[7:0] (Read/Write)
//        others  - reserved
// 0x14 : reserved
// 0x18 : Data signal of y_max
//        bit 7~0 - y_max[7:0] (Read/Write)
//        others  - reserved
// 0x1c : reserved
// 0x20 : Data signal of cr_min
//        bit 7~0 - cr_min[7:0] (Read/Write)
//        others  - reserved
// 0x24 : reserved
// 0x28 : Data signal of cr_max
//        bit 7~0 - cr_max[7:0] (Read/Write)
//        others  - reserved
// 0x2c : reserved
// 0x30 : Data signal of cb_min
//        bit 7~0 - cb_min[7:0] (Read/Write)
//        others  - reserved
// 0x34 : reserved
// 0x38 : Data signal of cb_max
//        bit 7~0 - cb_max[7:0] (Read/Write)
//        others  - reserved
// 0x3c : reserved
// 0x40 : Data signal of enable_morphology
//        bit 0  - enable_morphology[0] (Read/Write)
//        others - reserved
// 0x44 : reserved
// (SC = Self Clear, COR = Clear on Read, TOW = Toggle on Write, COH = Clear on Handshake)

#define XIMAGE_PREPROCESS_CONTROL_ADDR_AP_CTRL                0x00
#define XIMAGE_PREPROCESS_CONTROL_ADDR_GIE                    0x04
#define XIMAGE_PREPROCESS_CONTROL_ADDR_IER                    0x08
#define XIMAGE_PREPROCESS_CONTROL_ADDR_ISR                    0x0c
#define XIMAGE_PREPROCESS_CONTROL_ADDR_Y_MIN_DATA             0x10
#define XIMAGE_PREPROCESS_CONTROL_BITS_Y_MIN_DATA             8
#define XIMAGE_PREPROCESS_CONTROL_ADDR_Y_MAX_DATA             0x18
#define XIMAGE_PREPROCESS_CONTROL_BITS_Y_MAX_DATA             8
#define XIMAGE_PREPROCESS_CONTROL_ADDR_CR_MIN_DATA            0x20
#define XIMAGE_PREPROCESS_CONTROL_BITS_CR_MIN_DATA            8
#define XIMAGE_PREPROCESS_CONTROL_ADDR_CR_MAX_DATA            0x28
#define XIMAGE_PREPROCESS_CONTROL_BITS_CR_MAX_DATA            8
#define XIMAGE_PREPROCESS_CONTROL_ADDR_CB_MIN_DATA            0x30
#define XIMAGE_PREPROCESS_CONTROL_BITS_CB_MIN_DATA            8
#define XIMAGE_PREPROCESS_CONTROL_ADDR_CB_MAX_DATA            0x38
#define XIMAGE_PREPROCESS_CONTROL_BITS_CB_MAX_DATA            8
#define XIMAGE_PREPROCESS_CONTROL_ADDR_ENABLE_MORPHOLOGY_DATA 0x40
#define XIMAGE_PREPROCESS_CONTROL_BITS_ENABLE_MORPHOLOGY_DATA 1

