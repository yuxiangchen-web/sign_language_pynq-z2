# 原有 Python 源码阅读清单

所有下列文件已完整读取并解析；学习目录中的 DFF 不属于手语主工程。

| 路径 | 行数 | 定义的类和函数 |
|---|---:|---|
| `batch_hog_features.py` | 69 | 顶层学习脚本 |
| `batch_preprocess.py` | 140 | square_resize, make_skin_mask, process_one |
| `batch_preprocess_signs.py` | 70 | main |
| `binary_morphology_test.py` | 27 | 顶层学习脚本 |
| `camera_test.py` | 30 | 顶层学习脚本 |
| `capture_dataset.py` | 74 | 顶层学习脚本 |
| `capture_sequences.py` | 55 | main |
| `conftest.py` | 1 | 顶层学习脚本 |
| `contour_test.py` | 45 | 顶层学习脚本 |
| `dataset_audit.py` | 226 | read_manifest, file_hash, audit_manifest, main |
| `dataset_manifest.py` | 168 | load_metadata, collect_images, build_manifest |
| `evaluate_baseline.py` | 86 | 顶层学习脚本 |
| `evaluate_dynamic_model.py` | 79 | main |
| `evaluate_static_model.py` | 78 | main |
| `feature_utils.py` | 20 | hog_feature |
| `hog_feature_test.py` | 37 | 顶层学习脚本 |
| `image_test.py` | 26 | 顶层学习脚本 |
| `labels.py` | 94 | is_static_label, is_dynamic_label, is_valid_label, validate_confidence, make_result |
| `predictor.py` | 270 | load_config, _soft_confidence, StaticPredictor, DynamicPredictor, RealtimeSignPredictor |
| `preprocess.py` | 111 | segment_hand_ycrcb, largest_component, normalize_binary, preprocess_frame |
| `preprocess_test.py` | 13 | 顶层学习脚本 |
| `real_hand_test.py` | 69 | 顶层学习脚本 |
| `realtime_sign_pc.py` | 128 | build_audio_player, announce, frames_from_video, frames_from_dir, run_static, run_dynamic, main |
| `sequence_features.py` | 113 | sample_frames, _zero_features, _frame_features, extract_sequence_features |
| `skin_segmentation_test.py` | 124 | square_and_resize |
| `test_predictor.py` | 188 | make_frame, FakeStatic, FakeDynamic, make_rt, motion_clip, test_static_result_structure, test_dynamic_result_structure_and_seq_len_switch, test_static_and_dynamic_structure_consistent, test_unknown_judgment_low_confidence, test_unknown_passthrough, test_sequence_too_short_raises, test_feed_detects_action, test_feed_no_motion_returns_none, test_feed_no_hand_returns_none, test_feed_short_action_ignored, test_cooldown_and_repeat_suppression, test_unknown_not_suppressed_by_repeat |
| `test_preprocess.py` | 112 | make_frame, test_segment_hand_ycrcb_binary_values, test_preprocess_output_size, test_empty_input_raises, test_no_hand_returns_none, test_hand_touches_edge_flagged, test_normalize_binary_shape, test_make_result_valid, test_make_result_invalid, test_label_sets |
| `tests/test_predictor.py` | 202 | make_frame, FakeStatic, FakeDynamic, make_rt, motion_clip, test_static_result_structure, test_dynamic_result_structure_and_seq_len_switch, test_static_and_dynamic_structure_consistent, test_unknown_judgment_low_confidence, test_unknown_passthrough, test_sequence_too_short_raises, test_feed_detects_action, test_feed_no_motion_returns_none, test_feed_no_hand_returns_none, test_feed_short_action_ignored, test_cooldown_and_repeat_suppression, test_unknown_not_suppressed_by_repeat |
| `tests/test_preprocess.py` | 112 | make_frame, test_segment_hand_ycrcb_binary_values, test_preprocess_output_size, test_empty_input_raises, test_no_hand_returns_none, test_hand_touches_edge_flagged, test_normalize_binary_shape, test_make_result_valid, test_make_result_invalid, test_label_sets |
| `tests/test_role_c_audio.py` | 222 | write_test_wave, wav_dir, test_mapping_uses_b_labels, test_invalid_label_rejected, test_unknown_never_calls_player, test_b_compatibility_function, test_missing_corrupt_silent_truncated_wav, test_invalid_result, test_announcer_threshold_cooldown_repeat_and_close, test_full_queue_nonblocking_and_rejected_request_does_not_update_state, test_play_failure_reported_worker_continues, test_prepare_import_and_atomic_failure, test_offline_board_mapping, test_existing_b_audio_hook, test_invalid_audio_config, test_aplay_command_and_failure_propagation, test_close_timeout_can_be_retried, test_delivered_chinese_assets_and_manifest |
| `tests/test_role_c_benchmark.py` | 28 | test_cpu_measurement_is_explicitly_pc_only, test_invalid_cpu_inputs |
| `tests/test_role_c_dma.py` | 357 | fake_description, FakeClock, FakeBuffer, FakeChannel, FakeMMIO, FakeDMA, make_transfer, test_transaction_cache_order_and_independent_result, test_1000_continuous_transactions, test_bad_deadline, test_shape_dtype_rejected_before_dma, test_noncontiguous_input_copied_without_changing_format, test_missing_tlast_timeout_reset_and_no_faulted_reuse, test_dma_error_reset, test_failed_reset_quarantines_and_retry_allows_release, test_short_tlast_rejected_even_if_both_channels_idle, test_start_callback_failure_resets_armed_receiver, test_unsupported_configuration, test_missing_config_and_uppercase_parameter_names, test_invalid_shapes_or_length, test_allocation_failure_frees_first_buffer, test_misaligned_address_frees_both_buffers, test_wrong_golden_output_is_failure_not_silently_accepted, test_initial_halted_or_busy_channel_rejected, test_ready_driver_initial_idle_zero_allowed_on_first_transaction, test_physical_overlap_and_address_overflow_rejected |
| `tests/test_role_c_overlay.py` | 109 | FakeGpio, FakeOverlay, test_real_hwh_contract, test_fake_overlay_load_reload_and_missing_dma, test_loader_rejects_mismatch, test_gpio_patterns_and_restore, test_gpio_restore_even_on_readback_failure, test_missing_and_invalid_metadata, test_working_directory_independent |
| `train_baseline.py` | 67 | 顶层学习脚本 |
| `train_dynamic_model.py` | 129 | video_frames, load_dataset, build_classifier, main |
| `train_static_model.py` | 87 | load_features, evaluate, main |
