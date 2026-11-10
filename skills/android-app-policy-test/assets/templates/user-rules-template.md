# Rule kiểm thử Android

Checklist nền bắt buộc là `SKILL_DIR/references/dev-checklist.md`, được đóng gói cùng skill. Nếu cần thêm rule cho app, sao chép mẫu này vào `PROJECT_ROOT/checklists/additional-rules.md`; không ghi đè bản nền trong nơi cài skill. Thay các placeholder bằng rule thực tế; lặp lại khối cho mỗi rule. Nội dung ví dụ không tự trở thành yêu cầu của app.

Chỉ mô tả tiêu chí source/resources/cấu hình/dependency. Nếu yêu cầu gốc nói về runtime, giữ câu gốc để truy xuất nguồn và viết expected whitebox tương ứng; phần chỉ xác minh được bằng app, APK/AAB, Console hoặc backend nằm ở giới hạn, không tạo testcase. Giữ năm status PASS/FAIL/BLOCKED/NOT_TESTED/NOT_APPLICABLE theo hướng dẫn skill.

## USR-001 — <Tên rule>

- Nội dung gốc: <Giữ nguyên câu chữ người dùng cung cấp>
- Nguồn/phiên bản: <File, mục hoặc nội dung hội thoại>
- Điều kiện áp dụng: <Tính năng, variant, Android, nhóm người dùng>
- Tiền điều kiện: <Code, resources, cấu hình và tài liệu đối chiếu cần để review source>
- Tiêu chí kiểm chứng từ source: <Nhánh code, cấu hình hoặc xử lý lỗi phải có>
- Giới hạn kết luận: <Phần ngoài source; chỉ mô tả, không sinh testcase hoặc chặn tiêu chí source>
- Các bước:
  1. <Đường gọi/nhánh code hoặc resources/config cần đọc>
  2. <Điều kiện, state, callback và nhánh lỗi cần đối chiếu>
- Kết quả mong đợi: <Điều kiện đạt có bằng chứng trong source>
- Nhánh lỗi/ngoại lệ: <Từ chối quyền, hủy, mất mạng... nếu liên quan>
- Bằng chứng cần thu: <file:line, chuỗi gọi hàm, cấu hình hoặc kết quả lint/unit test>

## Ví dụ minh họa — chưa phải rule được xác nhận

- Nội dung gốc: Khi từ chối quyền camera, app không crash và cho phép thử lại.
- Điều kiện áp dụng: Source có tính năng chụp ảnh và code xin quyền camera.
- Tiền điều kiện: Đọc được permission callbacks và các entry point mở camera.
- Các bước: Truy vết check/request permission, callback denied và action thử lại; đọc điều kiện trước mọi đường mở camera.
- Kết quả mong đợi: Nhánh denied không mở camera, cập nhật state/thông báo và cung cấp action thử lại phù hợp trạng thái quyền trong code.
- Tiêu chí source: Có xử lý kết quả từ chối quyền, không tiếp tục mở camera khi chưa được cấp quyền và có luồng thử lại phù hợp.
- Bằng chứng: file:line của permission callback và luồng thử lại; unit test nếu có.
- Giới hạn kết luận: Không xác nhận app không crash trên thiết bị; không tạo case runtime để bổ sung.

Rule riêng của người dùng và yêu cầu Google Play được ghi thành hai nguồn độc lập. Ví dụ trên không tự chứng minh tuân thủ Permissions policy.
