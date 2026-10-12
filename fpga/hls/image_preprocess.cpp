#include "image_preprocess.h"

// 将整数限制到 0~255
static ap_uint<8> clamp_u8(int value) {
    if (value < 0) {
        return 0;
    }

    if (value > 255) {
        return 255;
    }

    return static_cast<ap_uint<8>>(value);
}

// RGB888 转换为近似 YCrCb
//
// 输入：
//   r、g、b：0~255
//
// 输出：
//   y、cr、cb：0~255
//
// 这里使用整数近似公式，避免 FPGA 中使用浮点运算。
static void rgb_to_ycrcb(
    ap_uint<8> r,
    ap_uint<8> g,
    ap_uint<8> b,
    ap_uint<8>& y,
    ap_uint<8>& cr,
    ap_uint<8>& cb
) {
    int r_i = static_cast<int>(r);
    int g_i = static_cast<int>(g);
    int b_i = static_cast<int>(b);

    int y_value =
        (77 * r_i + 150 * g_i + 29 * b_i) >> 8;

    int cr_value =
        ((131 * r_i - 110 * g_i - 21 * b_i) >> 8) + 128;

    int cb_value =
        ((-43 * r_i - 85 * g_i + 128 * b_i) >> 8) + 128;

    y = clamp_u8(y_value);
    cr = clamp_u8(cr_value);
    cb = clamp_u8(cb_value);
}

void image_preprocess(
    hls::stream<axis_rgb_t>& input_stream,
    hls::stream<axis_mask_t>& output_stream,

    ap_uint<8> y_min,
    ap_uint<8> y_max,
    ap_uint<8> cr_min,
    ap_uint<8> cr_max,
    ap_uint<8> cb_min,
    ap_uint<8> cb_max,

    ap_uint<1> enable_morphology
) {
#pragma HLS INTERFACE axis port=input_stream
#pragma HLS INTERFACE axis port=output_stream

#pragma HLS INTERFACE s_axilite port=y_min bundle=control
#pragma HLS INTERFACE s_axilite port=y_max bundle=control
#pragma HLS INTERFACE s_axilite port=cr_min bundle=control
#pragma HLS INTERFACE s_axilite port=cr_max bundle=control
#pragma HLS INTERFACE s_axilite port=cb_min bundle=control
#pragma HLS INTERFACE s_axilite port=cb_max bundle=control
#pragma HLS INTERFACE s_axilite port=enable_morphology bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control

    // 保存一帧二值化结果。
    // 当前尺寸为 360x360，共 129600 个像素。
    ap_uint<8> mask_frame[IMAGE_HEIGHT][IMAGE_WIDTH];

    // 第一阶段：读取 AXI-Stream，并进行 RGB → YCrCb → 阈值分割
    for (int row = 0; row < IMAGE_HEIGHT; row++) {
        for (int col = 0; col < IMAGE_WIDTH; col++) {
#pragma HLS PIPELINE II=1

            axis_rgb_t input_pixel = input_stream.read();

            ap_uint<8> r = input_pixel.data.range(23, 16);
            ap_uint<8> g = input_pixel.data.range(15, 8);
            ap_uint<8> b = input_pixel.data.range(7, 0);

            ap_uint<8> y;
            ap_uint<8> cr;
            ap_uint<8> cb;

            rgb_to_ycrcb(r, g, b, y, cr, cb);

            bool is_foreground =
                (y >= y_min) && (y <= y_max) &&
                (cr >= cr_min) && (cr <= cr_max) &&
                (cb >= cb_min) && (cb <= cb_max);

            mask_frame[row][col] =
                is_foreground ? static_cast<ap_uint<8>>(255)
                              : static_cast<ap_uint<8>>(0);
        }
    }

    // 第二阶段：输出结果。
    // enable_morphology=0 时直接输出阈值分割结果；
    // enable_morphology=1 时进行简单 3x3 多数滤波。
    for (int row = 0; row < IMAGE_HEIGHT; row++) {
        for (int col = 0; col < IMAGE_WIDTH; col++) {
#pragma HLS PIPELINE II=1

            ap_uint<8> output_value = mask_frame[row][col];

            if (enable_morphology != 0) {
                int foreground_count = 0;

                for (int dy = -1; dy <= 1; dy++) {
                    for (int dx = -1; dx <= 1; dx++) {
#pragma HLS UNROLL

                        int neighbor_row = row + dy;
                        int neighbor_col = col + dx;

                        if (neighbor_row >= 0 &&
                            neighbor_row < IMAGE_HEIGHT &&
                            neighbor_col >= 0 &&
                            neighbor_col < IMAGE_WIDTH) {

                            if (mask_frame[neighbor_row][neighbor_col] != 0) {
                                foreground_count++;
                            }
                        }
                    }
                }

                // 3x3 区域至少 5 个前景像素时保留为前景
                output_value =
                    (foreground_count >= 5)
                        ? static_cast<ap_uint<8>>(255)
                        : static_cast<ap_uint<8>>(0);
            }

            axis_mask_t output_pixel;

            output_pixel.data = output_value;
            output_pixel.keep = 1;
            output_pixel.strb = 1;
            output_pixel.user = (row == 0 && col == 0) ? 1 : 0;
            output_pixel.last =
                (row == IMAGE_HEIGHT - 1 &&
                 col == IMAGE_WIDTH - 1) ? 1 : 0;
            output_pixel.id = 0;
            output_pixel.dest = 0;

            output_stream.write(output_pixel);
        }
    }
}