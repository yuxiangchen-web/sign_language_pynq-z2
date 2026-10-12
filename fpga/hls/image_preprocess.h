#ifndef IMAGE_PREPROCESS_H
#define IMAGE_PREPROCESS_H

#include <ap_int.h>
#include <ap_axi_sdata.h>
#include <hls_stream.h>

// 当前正式静态图片尺寸为 360x360
constexpr int IMAGE_WIDTH = 360;
constexpr int IMAGE_HEIGHT = 360;
constexpr int IMAGE_PIXELS = IMAGE_WIDTH * IMAGE_HEIGHT;

// 输入：RGB888，每个像素 24 bit
// data[23:16] = R
// data[15:8]  = G
// data[7:0]   = B
using axis_rgb_t = ap_axiu<24, 1, 1, 1>;

// 输出：8 bit 二值掩膜
// 0 = 背景
// 255 = 前景
using axis_mask_t = ap_axiu<8, 1, 1, 1>;

// HLS 顶层函数
void image_preprocess(
    hls::stream<axis_rgb_t>& input_stream,
    hls::stream<axis_mask_t>& output_stream,

    // YCrCb 阈值配置，通过 AXI-Lite 写入
    ap_uint<8> y_min,
    ap_uint<8> y_max,
    ap_uint<8> cr_min,
    ap_uint<8> cr_max,
    ap_uint<8> cb_min,
    ap_uint<8> cb_max,

    // 1：启用简单形态学处理
    // 0：只进行阈值分割
    ap_uint<1> enable_morphology
);

#endif