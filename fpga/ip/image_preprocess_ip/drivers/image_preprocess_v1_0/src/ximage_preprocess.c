// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
/***************************** Include Files *********************************/
#include "ximage_preprocess.h"

/************************** Function Implementation *************************/
#ifndef __linux__
int XImage_preprocess_CfgInitialize(XImage_preprocess *InstancePtr, XImage_preprocess_Config *ConfigPtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(ConfigPtr != NULL);

    InstancePtr->Control_BaseAddress = ConfigPtr->Control_BaseAddress;
    InstancePtr->IsReady = XIL_COMPONENT_IS_READY;

    return XST_SUCCESS;
}
#endif

void XImage_preprocess_Start(XImage_preprocess *InstancePtr) {
    u32 Data;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_AP_CTRL) & 0x80;
    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_AP_CTRL, Data | 0x01);
}

u32 XImage_preprocess_IsDone(XImage_preprocess *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_AP_CTRL);
    return (Data >> 1) & 0x1;
}

u32 XImage_preprocess_IsIdle(XImage_preprocess *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_AP_CTRL);
    return (Data >> 2) & 0x1;
}

u32 XImage_preprocess_IsReady(XImage_preprocess *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_AP_CTRL);
    // check ap_start to see if the pcore is ready for next input
    return !(Data & 0x1);
}

void XImage_preprocess_EnableAutoRestart(XImage_preprocess *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_AP_CTRL, 0x80);
}

void XImage_preprocess_DisableAutoRestart(XImage_preprocess *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_AP_CTRL, 0);
}

void XImage_preprocess_Set_y_min(XImage_preprocess *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_Y_MIN_DATA, Data);
}

u32 XImage_preprocess_Get_y_min(XImage_preprocess *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_Y_MIN_DATA);
    return Data;
}

void XImage_preprocess_Set_y_max(XImage_preprocess *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_Y_MAX_DATA, Data);
}

u32 XImage_preprocess_Get_y_max(XImage_preprocess *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_Y_MAX_DATA);
    return Data;
}

void XImage_preprocess_Set_cr_min(XImage_preprocess *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_CR_MIN_DATA, Data);
}

u32 XImage_preprocess_Get_cr_min(XImage_preprocess *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_CR_MIN_DATA);
    return Data;
}

void XImage_preprocess_Set_cr_max(XImage_preprocess *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_CR_MAX_DATA, Data);
}

u32 XImage_preprocess_Get_cr_max(XImage_preprocess *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_CR_MAX_DATA);
    return Data;
}

void XImage_preprocess_Set_cb_min(XImage_preprocess *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_CB_MIN_DATA, Data);
}

u32 XImage_preprocess_Get_cb_min(XImage_preprocess *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_CB_MIN_DATA);
    return Data;
}

void XImage_preprocess_Set_cb_max(XImage_preprocess *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_CB_MAX_DATA, Data);
}

u32 XImage_preprocess_Get_cb_max(XImage_preprocess *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_CB_MAX_DATA);
    return Data;
}

void XImage_preprocess_Set_enable_morphology(XImage_preprocess *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_ENABLE_MORPHOLOGY_DATA, Data);
}

u32 XImage_preprocess_Get_enable_morphology(XImage_preprocess *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_ENABLE_MORPHOLOGY_DATA);
    return Data;
}

void XImage_preprocess_InterruptGlobalEnable(XImage_preprocess *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_GIE, 1);
}

void XImage_preprocess_InterruptGlobalDisable(XImage_preprocess *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_GIE, 0);
}

void XImage_preprocess_InterruptEnable(XImage_preprocess *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_IER);
    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_IER, Register | Mask);
}

void XImage_preprocess_InterruptDisable(XImage_preprocess *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_IER);
    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_IER, Register & (~Mask));
}

void XImage_preprocess_InterruptClear(XImage_preprocess *InstancePtr, u32 Mask) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XImage_preprocess_WriteReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_ISR, Mask);
}

u32 XImage_preprocess_InterruptGetEnabled(XImage_preprocess *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_IER);
}

u32 XImage_preprocess_InterruptGetStatus(XImage_preprocess *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XImage_preprocess_ReadReg(InstancePtr->Control_BaseAddress, XIMAGE_PREPROCESS_CONTROL_ADDR_ISR);
}

