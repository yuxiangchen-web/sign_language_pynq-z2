# Python / HLS comparison

Date: 2026-10-09

Used an existing RGB image resized to 360x360. Fixed input and expected
outputs are in fpga/hls/test_vectors; source.json records the image path.
Python uses the same integer coefficients, shifts, clipping and inclusive
thresholds as image_preprocess.cpp. Morphology uses zero-padded 3x3 voting.

| Morphology | Pixels | Mismatches | Difference rate |
| --- | --- | --- | --- |
| 0 | 129600 | 0 | 0% |
| 1 | 129600 | 0 | 0% |

Output count, USER, TLAST, KEEP and STRB were checked. Both frames were
processed consecutively by the same HLS function. CSim completed with
0 errors. This is one-image algorithm verification, not a board benchmark.

Reproduce from PowerShell:

```powershell
cd D:\PYNQ\projects\sign-language-pynq
.\.venv\Scripts\python.exe .\software\prepare_compare.py
& 'D:\AMDTools\2026.1\Vitis\bin\vitis-run.bat' --mode hls --tcl .\fpga\hls\run_compare.tcl
```

No synthesis, IP export or bitstream generation is performed.
Detailed log: fpga/hls/compare_hls/solution1/csim/report/image_preprocess_csim.log.
