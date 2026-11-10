# Screenshot và bằng chứng lỗi automation

Chỉ thu ảnh từ lần thực thi thực tế. Không cần framework golden/pixel comparison
để lưu screenshot lỗi. Dùng cơ chế của framework hiện có nếu đã thu được ảnh đúng
case/bước; nếu thiếu, thêm helper trong test source set.

## Capture trước cleanup

- Với instrumentation JUnit4, có thể thích nghi
  [helper test-only](../assets/templates/FailureEvidence.kt). Thay package placeholder
  bằng package test, dùng runner arguments/run metadata thực tế. Helper dùng AndroidX
  Test hiện có, không cần sửa resource, manifest hoặc code production.
- Đặt wrapper checkpoint **bên trong** scope ActivityScenario/FragmentScenario,
  bao quanh action và assertion, để catch lỗi trước `.use`/rule đóng màn hình.
  Đặt watcher ngoài ActivityScenarioRule có thể quá muộn; xác minh thứ tự rules.
- Checkpoint gồm thao tác và expected, không chỉ số thứ tự click. Ghi ID checkpoint
  trong artifact và báo cáo; workflow dài có checkpoint gần thao tác rủi ro.
- Helper lưu PNG và metadata run/case/attempt/checkpoint/time/device vào external
  files của test target. Pull file về evidence đúng run trước khi gỡ APK/reset data.
  Timestamp/serial/mapping thực tế phải đi cùng ảnh trong report.
- Capture thất bại phải giữ nguyên exception gốc; lưu lỗi capture riêng hoặc
  suppressed exception. Không đánh PASS vì đã chụp được ảnh trước assertion fail.

## Crash và tái hiện

- Process chết có thể không chạy hook trong app. Runner phía host lưu instrumentation
  output, stacktrace/logcat và thử screenshot qua ADB khi thiết bị còn kết nối.
  Dùng adb đã phát hiện trong SDK, chọn serial cụ thể; không tự chọn giữa nhiều máy.
- Sau crash, lệnh `adb -s <serial> exec-out screencap -p` có thể chụp launcher/dialog
  hệ thống. Gắn timing `after_crash`, không mô tả ảnh đó như UI lỗi trước crash.
  Ảnh checkpoint trước đó dùng `before_crash` với bước/thời gian đúng thực tế.
- Nếu lần đầu thiếu ảnh, cho phép tối đa một attempt riêng của case để tái hiện
  nhằm thu evidence, cùng fixture/config/source và expected. Giữ nguyên kết quả lần
  đầu; attempt sau PASS không xóa FAIL. Nếu môi trường không cho phép retry, ghi lý do.
- Không tái hiện bằng cách đổi source, bỏ assertion, thay expected hoặc thao tác
  giao dịch production không thuộc phạm vi được phép. Dùng môi trường test/sandbox.

## Ghi nhận khi thiếu ảnh

- JVM test không có UI: `not_applicable`, ghi lý do và log assertion/stacktrace.
- UI có FLAG_SECURE, device disconnect, process crash trước capture, lỗi ghi/pull
  ảnh hoặc không tái hiện lại được: `unavailable`, ghi nguyên nhân và attempts đã làm.
  Không sửa FLAG_SECURE hay app để cho phép capture.
- Đường dẫn PNG tương đối từ RUN_DIR phải ở đúng case/attempt; không dùng absolute path, `..`, symlink hoặc hardlink dùng chung. File ảnh độc lập giống nội dung vẫn hợp lệ.
- Failure có PNG dùng `captured`; metadata từng ảnh gồm checkpoint và timing.
  Nếu chỉ có ảnh sau crash, report nói rõ giá trị bằng chứng hạn chế của ảnh.
- Từ trang chi tiết case dẫn đường dẫn tương đối và hiển thị ảnh lỗi khi có.
  Screenshot không thay runner log/expected/actual; lỗi capture không tạo lỗi app mới.
