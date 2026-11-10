# Nguồn và phạm vi Google Play policy

Đây là chỉ mục kiểm tra source, không phải bản sao toàn bộ chính sách. Mỗi lần dùng phải mở nguồn hiện hành, đọc điều khoản và ngoại lệ áp dụng. Chỉ tạo case cho tiêu chí cụ thể kiểm chứng được từ code, resources, cấu hình hoặc dependencies; PASS của case không xác nhận toàn bộ nhóm policy.

Console declarations/approval, store listing, backend practices, nội dung được phân phối và trải nghiệm runtime chỉ ghi trong giới hạn. Không tạo case riêng cho chúng, không dùng thiếu dữ liệu đó để chặn tiêu chí source độc lập. Nếu dữ liệu thiếu thực sự quyết định applicability/ngoại lệ của một tiêu chí source, ghi BLOCKED cho phần đó và nêu chính xác dữ liệu cần thiết. Không tạo case APK/AAB, binary alignment hoặc build/cài/chạy artifact.

## Điểm bắt đầu

- [Developer Policy Center](https://play.google/developer-content-policy/): duyệt toàn bộ nhóm và tìm thêm điều khoản theo tính năng app.
- Từ Policy Center, kiểm tra thông báo cập nhật, ngày hiệu lực và bản preview nếu có. Tách yêu cầu hiện tại khỏi rủi ro cho ngày phát hành dự kiến.
- Tài liệu Android tại `developer.android.com` giải thích kỹ thuật; chỉ gọi một lỗi kỹ thuật là vi phạm Play khi có điều khoản Play tương ứng.

## Dữ liệu và quyền

- [User Data](https://support.google.com/googleplay/android-developer/answer/10144311): truy vết dữ liệu từ entry point tới request/storage/SDK calls; kiểm tra code/resource disclosure, consent, liên kết privacy policy và đường xóa tài khoản khi áp dụng. Không xác nhận nội dung URL hoặc backend thực tế từ việc có đường dẫn/call site.
- [Permissions and APIs that Access Sensitive Information](https://support.google.com/googleplay/android-developer/answer/16558241): đối chiếu quyền/API với tính năng, ngữ cảnh xin quyền, mục đích và giới hạn riêng của từng loại quyền.
- Tìm trang Data safety và account deletion liên quan để hiểu điều khoản source đang áp dụng; bản khai Console và retention/sharing/security phía server nằm ngoài kết luận source, không sinh case xác nhận chúng.

## Quảng cáo và thanh toán

- [Ads](https://support.google.com/googleplay/android-developer/answer/9857753): truy vết placement/layout, điều kiện, timer/counter và callback trong source theo điều khoản cụ thể. Nội dung quảng cáo được trả về, fill và timing quan sát thực tế chỉ là giới hạn, không tạo case chưa chạy.
- [Payments](https://support.google.com/googleplay/android-developer/answer/9858738): xác định sản phẩm số/vật lý, thị trường, chương trình và ngoại lệ trước khi đánh giá phương thức thanh toán.
- Nếu có subscription, mở policy Subscriptions từ Policy Center; đối chiếu code/resources của tên, giá, chu kỳ, trial, luồng hủy và mapping product/offer token. Không tạo case giao dịch hoặc đối chiếu dialog Google thực tế.

## Phát hành và trải nghiệm

- [Target API Level](https://support.google.com/googleplay/android-developer/answer/16561298): theo liên kết hướng dẫn chi tiết để xác minh mốc hiện hành, loại app và ngoại lệ. Ghi target SDK có hiệu lực trong cấu hình variant; không yêu cầu manifest từ artifact.
- [Functionality, Content, and User Experience](https://support.google.com/googleplay/android-developer/answer/9898783): tìm lỗi logic, luồng lỗi và chức năng thiếu trong source. Không khẳng định trải nghiệm thực tế đạt nếu chưa chạy app.
- Từ Policy Center, mở Deceptive Behavior, SDK Requirements, Device and Network Abuse và nhóm liên quan để xác định tiêu chí source. Metadata, Content Ratings và store listing không có trong source chỉ được nêu là giới hạn, không sinh case BLOCKED vì thiếu Console/listing.

## Nhóm có điều kiện

- [Families](https://support.google.com/googleplay/android-developer/answer/9893335): dùng căn cứ audience có trong source hoặc đầu vào được cung cấp để đối chiếu code cấu hình dữ liệu, ads và SDK. Không suy ra target audience Console từ một câu text trong app.
- Với UGC, AI-generated content, health, finance, gambling hoặc thiết bị đặc thù, mở nhóm tương ứng từ Policy Center; chỉ bổ sung case cho feature và tiêu chí source cụ thể. Không tạo case yêu cầu khai báo Console hoặc hành vi server.
- Nếu chưa biết tính năng có tồn tại, tiếp tục truy vết source; nếu cần đầu vào quyết định applicability mà không có, ghi BLOCKED cho tiêu chí source. Chỉ dùng `NOT_APPLICABLE` khi có căn cứ; thiếu dữ liệu không đồng nghĩa không áp dụng.

## Hồ sơ nguồn cho mỗi yêu cầu

Ghi ID, URL trang/điều khoản cụ thể, tiêu đề mục, ngày truy cập, ngày hiệu lực nếu có, expected source, ngoại lệ và căn cứ áp dụng. Nếu nguồn chính thức cần cho tiêu chí source không truy cập được hoặc mâu thuẫn chưa giải quyết, dùng BLOCKED và ghi điều kiện tiếp tục; không bịa chính sách. Ghi riêng giới hạn kết luận ngoài source.
