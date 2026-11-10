## Cách dùng cấu trúc rule

- Cấu trúc tham chiếu: [user-rules-template.md](../assets/templates/user-rules-template.md). Giữ nguyên ID `DEV-xxx`, thứ tự, nhóm và nội dung gốc để truy xuất nguồn; không chuyển thành ID `USR`.
- Checklist gồm 32 rule whitebox. DEV-034 và DEV-037 đã loại bỏ vì phụ thuộc tài liệu ads Lutech riêng; không đánh lại số hoặc khôi phục hai rule này khi sinh case.
- Nội dung gốc và số dòng sheet chỉ ghi xuất xứ. Kết quả mong đợi và bước kiểm tra hiện tại chỉ áp dụng cho source, resources, cấu hình và dependencies; không dùng yêu cầu runtime gốc làm tiêu chí đạt.
- Không tạo case chạy app/thiết bị, giao dịch thực tế, nội dung server được phân phối, kiểm tra APK/AAB, binary alignment hoặc build/cài/chạy artifact. Chỉ mô tả giới hạn của kết luận nếu cần.
- Có thể dùng lint, local unit tests, dependency graph và merged manifest sẵn có hoặc tạo bởi các task kiểm tra source được phép; không yêu cầu assemble/bundle hay task chạy thiết bị. Thiếu APK, thiết bị hoặc tài khoản giao dịch không chặn case source.
- Mỗi rule còn lại có kết quả `PASS`, `FAIL`, `BLOCKED`, `NOT_TESTED` hoặc `NOT_APPLICABLE`. PASS/FAIL cần bằng chứng đủ cho tiêu chí source; BLOCKED cần chỉ rõ đầu vào/công cụ thiếu cho chính tiêu chí đó; NOT_TESTED chỉ dùng cho kiểm tra source chưa bắt đầu hoặc chưa hoàn tất; NOT_APPLICABLE cần căn cứ điều kiện không đúng với app.
- Tiền điều kiện nêu nơi cần đọc, không phải lý do bỏ qua triển khai bị thiếu: nếu đọc đủ source và xác định không có callback/config bắt buộc thì FAIL; không đọc được file hoặc thiếu nguồn đối chiếu cần thiết mới là BLOCKED. Tính năng không tồn tại chỉ là NOT_APPLICABLE khi rule có điều kiện tương ứng.
- Dùng `rg` để định vị rồi đọc ngữ cảnh và xem tài nguyên local. Chưa review hết code/ảnh không tự là BLOCKED; tiếp tục review, hoặc ghi NOT_TESTED và mức thực hiện Một phần nếu dừng khi chưa hoàn tất mà không có blocker cụ thể.
- Ghi bằng chứng file:line, chuỗi entry point → điều kiện → hành động → lỗi, tập resources đã xem và lệnh/exit code nếu thực sự chạy. Không suy ra hành vi runtime hoặc toàn bộ tuân thủ Google Play từ PASS source; checkbox không thay bằng chứng.
- Tiếp tục tra tài liệu SDK/policy công khai chính thức cho tiêu chí cần đối chiếu; phân biệt rule nội bộ với policy. Các ví dụ là giả định, không phải kết quả app hoặc yêu cầu mới.

## 1. FUNCTION Testing

### 1.4. Internet / Remote Config / Config Update

- [ ] **DEV-016 — Internet** (dòng 22 trong sheet)
  - Nội dung gốc: Test có internet
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 22 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: Các tính năng có sử dụng mạng trong app.
  - Tiền điều kiện: Có API client/repository, model response và code quản lý loading/success/error của các flow cần mạng.
  - Tiêu chí kiểm chứng từ source: Truy vết từng flow cần mạng từ action UI qua API client/repository đến mapping response và nơi cập nhật state. Đọc nhánh success, response rỗng, exception và callback sau khi màn hình đóng; đối chiếu việc kết thúc loading và action tiếp theo.
  - Các bước:
    1. Truy vết từng flow cần mạng từ action UI qua API client/repository đến mapping response và nơi cập nhật state.
    2. Đọc nhánh success, response rỗng, exception và callback sau khi màn hình đóng; đối chiếu việc kết thúc loading và action tiếp theo.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Các nhánh response hợp lệ ánh xạ dữ liệu và cập nhật state/action đúng flow; lỗi HTTP, timeout, response rỗng và callback muộn có đường xử lý kết thúc loading hoặc chuyển sang state lỗi phù hợp.
  - Nhánh lỗi/ngoại lệ: Response rỗng, lỗi HTTP, timeout hoặc kết quả về muộn.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: API client có catch nhưng không chuyển state khỏi loading ở nhánh lỗi là bằng chứng source cần đánh giá; không cần gọi server thật.

- [ ] **DEV-017 — Offline** (dòng 23 trong sheet)
  - Nội dung gốc: Test không có internet
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 23 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: Flow cần xử lý trạng thái không có internet.
  - Tiền điều kiện: Có source xử lý lỗi kết nối, cache/fallback, thông báo và retry của các flow cần mạng.
  - Tiêu chí kiểm chứng từ source: Tìm điểm phát sinh lỗi kết nối và lần theo exception/result qua repository, ViewModel tới UI state. Đọc nhánh cache có/rỗng, retry và hủy request; kiểm tra không tiếp tục dùng dữ liệu null hoặc bỏ rơi loading.
  - Các bước:
    1. Tìm điểm phát sinh lỗi kết nối và lần theo exception/result qua repository, ViewModel tới UI state.
    2. Đọc nhánh cache có/rỗng, retry và hủy request; kiểm tra không tiếp tục dùng dữ liệu null hoặc bỏ rơi loading.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Nhánh mất kết nối/timeout được truyền tới state hoặc fallback có kiểm soát; loading được kết thúc, cache rỗng được xử lý và retry không lặp vô hạn ngoài chủ đích.
  - Nhánh lỗi/ngoại lệ: Mất mạng giữa request, cache rỗng hoặc retry nhiều lần.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Đọc nhánh IOException dẫn tới error state và retry; không yêu cầu bật/tắt mạng trên thiết bị.

### 1.6. Content Safety (Theme / Sticker / Image App)

- [ ] **DEV-024 — Image Review** (dòng 32 trong sheet)
  - Nội dung gốc: Kiểm tra content ảnh trong app
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 32 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có nội dung ảnh/theme/sticker hoặc nội dung ảnh tải từ dịch vụ.
  - Tiền điều kiện: Có resources/assets ảnh local đọc được và code khai báo, tải hoặc chọn nguồn ảnh động.
  - Tiêu chí kiểm chứng từ source: Liệt kê và xem ảnh local được app tham chiếu; ghi rõ tập tài nguyên đã xem, không thay xem ảnh bằng tìm tên file. Truy vết URL/catalog/config đến điểm tải và hiển thị ảnh; ghi giới hạn nội dung server ở phần phạm vi, không tạo case kiểm tra ảnh được phân phối thực tế.
  - Các bước:
    1. Liệt kê và xem ảnh local được app tham chiếu; ghi rõ tập tài nguyên đã xem, không thay xem ảnh bằng tìm tên file.
    2. Truy vết URL/catalog/config đến điểm tải và hiển thị ảnh; ghi giới hạn nội dung server ở phần phạm vi, không tạo case kiểm tra ảnh được phân phối thực tế.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Ảnh local trong phạm vi đã được xem và không trái tiêu chí nội dung áp dụng; code tải/chọn ảnh động được truy vết tới nguồn và cơ chế xử lý có trong repository. Không kết luận nội dung server thực tế an toàn từ URL.
  - Nhánh lỗi/ngoại lệ: Ảnh trong archive/dependency, catalog động, nội dung không đủ dữ liệu để đánh giá.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Có thể kết luận phần asset local sau khi xem đủ ảnh; catalog server không có trong source là giới hạn của kết luận, không phải case runtime.

- [ ] **DEV-025 — Violence** (dòng 33 trong sheet)
  - Nội dung gốc: Không có súng, thuốc lá, bạo lực
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 33 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: Kho nội dung ảnh, sticker, theme và tài nguyên liên quan theo yêu cầu dự án.
  - Tiền điều kiện: Có ảnh local đọc được, vị trí sử dụng và code xử lý nguồn nội dung ảnh.
  - Tiêu chí kiểm chứng từ source: Xem các ảnh local được dùng trong app và đối chiếu trực tiếp với súng, thuốc lá, bạo lực; dẫn file cụ thể nếu có. Truy vết nguồn nội dung động và ghi phần không nằm trong source; chỉ yêu cầu làm rõ nếu gặp nội dung thực sự không thể phân loại theo rule.
  - Các bước:
    1. Xem các ảnh local được dùng trong app và đối chiếu trực tiếp với súng, thuốc lá, bạo lực; dẫn file cụ thể nếu có.
    2. Truy vết nguồn nội dung động và ghi phần không nằm trong source; chỉ yêu cầu làm rõ nếu gặp nội dung thực sự không thể phân loại theo rule.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Tập ảnh local đã xem không có súng, thuốc lá hoặc bạo lực theo rule nội bộ; code xử lý nguồn ảnh động được mô tả theo phạm vi source, không xác nhận nội dung bên ngoài repository.
  - Nhánh lỗi/ngoại lệ: Tên file trung tính nhưng ảnh vi phạm; asset chưa được truy cập hoặc giải mã.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Ảnh local có súng là bằng chứng cho rule nội bộ; thiếu định nghĩa mức độ bạo lực không ngăn review các ảnh có nội dung rõ ràng.

- [ ] **DEV-026 — Sensitive Gesture** (dòng 34 trong sheet)
  - Nội dung gốc: Không có ngón tay thối / offensive gesture
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 34 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có ảnh/sticker/gesture hoặc nội dung liên quan.
  - Tiền điều kiện: Có ảnh/sticker/gesture local đọc được và các nơi tham chiếu trong source.
  - Tiêu chí kiểm chứng từ source: Xem ảnh/sticker/gesture local, gồm các frame hoặc sprite đọc được, và xác định nơi sử dụng. Đọc code tải/chọn nội dung động; dẫn asset cụ thể khi thấy gesture bị cấm và ghi giới hạn nếu nội dung nằm ngoài source.
  - Các bước:
    1. Xem ảnh/sticker/gesture local, gồm các frame hoặc sprite đọc được, và xác định nơi sử dụng.
    2. Đọc code tải/chọn nội dung động; dẫn asset cụ thể khi thấy gesture bị cấm và ghi giới hạn nếu nội dung nằm ngoài source.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Tập ảnh/sticker local đã xem không có ngón tay thối hoặc offensive gesture theo rule gốc; cơ chế lấy nội dung động được truy vết, không suy ra nội dung server thực tế.
  - Nhánh lỗi/ngoại lệ: Ảnh dạng sprite/animated, nội dung nhúng trong gói asset.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Tên sticker trung tính không chứng minh nội dung đạt; phải xem ảnh local trước khi kết luận.

- [ ] **DEV-027 — Sensitive Text** (dòng 35 trong sheet)
  - Nội dung gốc: Không chứa từ cấm như bitch, bad bitch
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 35 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: Text trong tài nguyên và nội dung app theo rule riêng.
  - Tiền điều kiện: Có strings/code/assets text và danh sách từ cấm được cung cấp nếu có.
  - Tiêu chí kiểm chứng từ source: Tìm từ cấm trong resources, code, assets và bản dịch; đọc ngữ cảnh và nơi hiển thị các match. Kiểm tra chuỗi ghép/nội suy và nguồn text động; ghi danh sách từ, phạm vi tìm kiếm và phần text không có trong repository.
  - Các bước:
    1. Tìm từ cấm trong resources, code, assets và bản dịch; đọc ngữ cảnh và nơi hiển thị các match.
    2. Kiểm tra chuỗi ghép/nội suy và nguồn text động; ghi danh sách từ, phạm vi tìm kiếm và phần text không có trong repository.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Text local đã review không chứa từ cấm của rule (gồm bitch, bad bitch); đã đọc ngữ cảnh, biến thể hoa/thường, bản dịch và chuỗi ghép. Kết luận chỉ bao phủ text và danh sách từ thực sự kiểm tra.
  - Nhánh lỗi/ngoại lệ: Biến thể chữ hoa/thường, bản dịch, chuỗi ghép và ngữ cảnh không phải nội dung app.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Không có match chỉ hỗ trợ kết luận trên tập text và danh sách từ đã rà; không chứng minh mọi nội dung server đều đạt.

## 2. ADS Testing

- [ ] **DEV-035 — Rewarded (nếu có)** (dòng 46 trong sheet)
  - Nội dung gốc: Reward callback đúng logic
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 46 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có Rewarded ads.
  - Tiền điều kiện: Có entry points Rewarded, reward callback và mapping phần thưởng trong source.
  - Tiêu chí kiểm chứng từ source: Truy vết từ load/show Rewarded đến callback reward và nơi cập nhật số dư/entitlement. Đọc nhánh dismiss, error, callback lặp và màn hình đã đóng; đối chiếu mapping phần thưởng với cấu hình tính năng.
  - Các bước:
    1. Truy vết từ load/show Rewarded đến callback reward và nơi cập nhật số dư/entitlement.
    2. Đọc nhánh dismiss, error, callback lặp và màn hình đã đóng; đối chiếu mapping phần thưởng với cấu hình tính năng.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Phần thưởng được cấp đúng loại/số lượng từ callback reward hợp lệ, không cấp từ dismiss/load error; callback lặp và thay đổi lifecycle không làm cấp thưởng sai theo flow.
  - Nhánh lỗi/ngoại lệ: Dismiss trước reward, callback trùng, màn hình đóng trong khi xem ads.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Cộng coin trong onDismiss thay vì callback reward là lỗi có thể xác định từ source; không cần xem quảng cáo thật.

- [ ] **DEV-036 — Real Ads** (dòng 47 trong sheet)
  - Nội dung gốc: Đảm bảo ads đang trả về là ads real
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 47 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: Variant release có quảng cáo.
  - Tiền điều kiện: Có ad unit, cấu hình test device, build type/flavor và code override/remote config trong source.
  - Tiêu chí kiểm chứng từ source: Tính đường chọn ad unit và chế độ test cho variant release qua Gradle, constants, resources và code init. Truy vết fallback, flavor và remote-config defaults; đối chiếu sample ID với nguồn SDK chính thức, ghi giá trị override không biết nếu ảnh hưởng tiêu chí.
  - Các bước:
    1. Tính đường chọn ad unit và chế độ test cho variant release qua Gradle, constants, resources và code init.
    2. Truy vết fallback, flavor và remote-config defaults; đối chiếu sample ID với nguồn SDK chính thức, ghi giá trị override không biết nếu ảnh hưởng tiêu chí.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Cấu hình release không chọn sample/test ad unit hoặc test-device mode; mọi fallback/override xác định được từ source đều phù hợp cấu hình production. Không xác nhận ad response hoặc fill.
  - Nhánh lỗi/ngoại lệ: Release dùng nhầm cấu hình debug, fallback về sample ID, cấu hình bị override.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Release trỏ tới sample ad unit là bằng chứng source; chưa có ad response không phải lỗi của case này.

- [ ] **DEV-038 — Ad Inspector** (dòng 49 trong sheet)
  - Nội dung gốc: Dùng Ad Inspector để debug ads không trả về
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 49 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có ads và cần chẩn đoán không trả về quảng cáo.
  - Tiền điều kiện: Có source tích hợp ads, đường diagnostic và callback lỗi load/show liên quan.
  - Tiêu chí kiểm chứng từ source: Tìm entry point diagnostic/Ad Inspector và lần theo callback lỗi của flow quảng cáo cần chẩn đoán. Đọc cách giữ/truyền mã lỗi, domain và cause; đối chiếu mapping lỗi có trong code với tài liệu SDK chính thức.
  - Các bước:
    1. Tìm entry point diagnostic/Ad Inspector và lần theo callback lỗi của flow quảng cáo cần chẩn đoán.
    2. Đọc cách giữ/truyền mã lỗi, domain và cause; đối chiếu mapping lỗi có trong code với tài liệu SDK chính thức.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Đường gọi diagnostic khi áp dụng và đường truyền mã lỗi được nối tới callback/log phù hợp; code giữ đủ domain/code/cause hoặc dữ liệu tương đương để đối chiếu No Fill với lỗi integration theo SDK. Không kết luận Inspector thực tế báo gì.
  - Nhánh lỗi/ngoại lệ: Chưa có dữ liệu lỗi, không đủ điều kiện mở Inspector hoặc lỗi integration.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Có lời gọi mở Inspector chỉ chứng minh đường tích hợp; không tạo yêu cầu mở app để xác nhận No Fill.

## 3. MEDIATION Testing

chỉ test phần này cho app có Ads

- [ ] **DEV-039 — Adapter Coverage** (dòng 51 trong sheet)
  - Nội dung gốc: App phải chứa đủ mediation adapters required
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 51 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: Chỉ app có Ads, theo điều kiện cấp nhóm MEDIATION Testing.
  - Tiền điều kiện: Có dependencies khai báo, flavor/variant và dependency graph release nếu đã resolve.
  - Tiêu chí kiểm chứng từ source: Liệt kê adapter của tám network trong Gradle/catalog và cấu hình dependency theo variant. Đối chiếu graph resolve nếu có, exclusions và resolution rules; xác định adapter thiếu hoặc chỉ tồn tại ở debug.
  - Các bước:
    1. Liệt kê adapter của tám network trong Gradle/catalog và cấu hình dependency theo variant.
    2. Đối chiếu graph resolve nếu có, exclusions và resolution rules; xác định adapter thiếu hoặc chỉ tồn tại ở debug.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Cấu hình dependency release chứa các adapter theo rule nội bộ: Meta, Pangle, Vungle, Unity, ironSource, AppLovin, Mintegral, InMobi; không dùng adapter chỉ ở debug để kết luận release đủ.
  - Nhánh lỗi/ngoại lệ: Dependency chỉ tồn tại ở debug, bị exclude hoặc resolve khác khai báo.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Meta chỉ khai báo ở debugImplementation không đáp ứng adapter coverage của release.

- [ ] **DEV-040 — SDK Version** (dòng 52 trong sheet)
  - Nội dung gốc: Tất cả mediation SDK / adapter ở version mới nhất
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 52 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: Chỉ app có Ads và mediation SDK/adapter trong phạm vi.
  - Tiền điều kiện: Có catalog/dependency configuration, graph resolve nếu có và nguồn release notes chính thức truy cập được.
  - Tiêu chí kiểm chứng từ source: Liệt kê version khai báo, constraints/resolution rules và version resolve của SDK/adapter nếu có graph. Đối chiếu từng version với release notes chính thức tại ngày review; phân biệt stable, prerelease và version bị ép.
  - Các bước:
    1. Liệt kê version khai báo, constraints/resolution rules và version resolve của SDK/adapter nếu có graph.
    2. Đối chiếu từng version với release notes chính thức tại ngày review; phân biệt stable, prerelease và version bị ép.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Version mediation SDK/adapter có hiệu lực trong dependency configuration được đối chiếu bản stable mới nhất tại ngày review; ghi rõ version, URL và ngày. Không có nguồn xác minh thì BLOCKED phần so sánh, không tạo case chạy app.
  - Nhánh lỗi/ngoại lệ: Version động, prerelease, version bị ép bởi resolution strategy.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Graph resolve version cũ hơn catalog phải được nêu rõ; đối chiếu version không cần case runtime.

- [ ] **DEV-041 — SDK Compatibility** (dòng 53 trong sheet)
  - Nội dung gốc: Adapter version compatible với mediation core SDK
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 53 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: Chỉ app có Ads và mediation core/adapter.
  - Tiền điều kiện: Có cấu hình/version resolve của core SDK, adapters và compatibility matrix hoặc release notes chính thức.
  - Tiêu chí kiểm chứng từ source: Lập danh sách các cặp core SDK/adapter sau constraints, transitive dependencies và resolution rules. Đọc matrix/release notes chính thức cho từng cặp; ghi nguồn, cặp đạt, cặp trái hỗ trợ hoặc cặp thiếu thông tin.
  - Các bước:
    1. Lập danh sách các cặp core SDK/adapter sau constraints, transitive dependencies và resolution rules.
    2. Đọc matrix/release notes chính thức cho từng cặp; ghi nguồn, cặp đạt, cặp trái hỗ trợ hoặc cặp thiếu thông tin.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Các cặp core SDK/adapter có hiệu lực được đối chiếu với hỗ trợ công bố; mỗi cặp có bằng chứng tương thích hoặc lỗi cụ thể, phần thiếu nguồn được ghi BLOCKED. Không yêu cầu khởi tạo/request ads thực tế.
  - Nhánh lỗi/ngoại lệ: Core bị nâng version bắc cầu, adapter khác nhau yêu cầu core khác nhau.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Hai adapter yêu cầu core khác nhau phải được đối chiếu với core thực sự resolve, không đoán từ khai báo.

- [ ] **DEV-042 — Ad Inspector** (dòng 54 trong sheet)
  - Nội dung gốc: Verify toàn bộ mediation adapters bằng Ad Inspector
    Đối với Dev:
    - Launch programmatically.
    Đối với Tester/PO/UA:
    - Launch using gestures
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 54 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: Chỉ app có Ads, cần verify mediation bằng Ad Inspector.
  - Tiền điều kiện: Có code/config diagnostic, danh sách adapter required và cấu hình SDK trong source.
  - Tiêu chí kiểm chứng từ source: Truy vết entry point mở Inspector bằng code và cấu hình gesture/test-device liên quan theo hướng dẫn SDK. Đối chiếu danh sách adapter với dependencies và init/config; kiểm tra đường diagnostic có thể được gọi theo điều kiện trong source.
  - Các bước:
    1. Truy vết entry point mở Inspector bằng code và cấu hình gesture/test-device liên quan theo hướng dẫn SDK.
    2. Đối chiếu danh sách adapter với dependencies và init/config; kiểm tra đường diagnostic có thể được gọi theo điều kiện trong source.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Có đường mở Inspector theo vai trò được rule gốc yêu cầu: programmatic cho dev, cấu hình gesture cho tester/PO/UA theo SDK; adapter configuration và đường init phù hợp variant. Không yêu cầu quan sát network list thực tế.
  - Nhánh lỗi/ngoại lệ: Inspector không mở, network thiếu hoặc adapter báo lỗi.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Có đủ dependencies không thay thế kiểm tra đường mở diagnostic; không cần chạy Inspector để đánh giá cơ chế tích hợp.

## 4. IAP Testing

- [ ] **DEV-043 — Purchase Success** (dòng 56 trong sheet)
  - Nội dung gốc: Mua IAP thành công phải có action xử lý đúng
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 56 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có IAP/subscription hoặc sản phẩm mua trong app.
  - Tiền điều kiện: Có purchase callbacks, product mapping và action sau mua trong source.
  - Tiêu chí kiểm chứng từ source: Truy vết kết quả Billing qua kiểm tra purchase state/validation đến cấp quyền và action UI. Đối chiếu product mapping, nhánh pending/cancel/error, callback lặp và callback sau khi màn hình đóng.
  - Các bước:
    1. Truy vết kết quả Billing qua kiểm tra purchase state/validation đến cấp quyền và action UI.
    2. Đối chiếu product mapping, nhánh pending/cancel/error, callback lặp và callback sau khi màn hình đóng.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Chỉ purchase hợp lệ ở trạng thái được phép cấp quyền mới cập nhật entitlement/coin và action đúng sản phẩm; pending/canceled/error không đi nhánh thành công, callback lặp không cấp quyền sai.
  - Nhánh lỗi/ngoại lệ: Purchase pending, user canceled, callback về sau khi màn hình đóng.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Callback success đặt premium trước khi kiểm tra purchase state là lỗi source, không cần tài khoản giao dịch.

- [ ] **DEV-044 — Premium Unlock** (dòng 57 trong sheet)
  - Nội dung gốc: Sau khi mua sub/in-app, toàn bộ premium feature được mở
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 57 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có premium entitlement từ subscription/in-app purchase.
  - Tiền điều kiện: Có danh sách premium features xác định từ source/resources và entitlement model dùng cho feature gates.
  - Tiêu chí kiểm chứng từ source: Lập danh sách premium features và mọi gate từ màn hình, navigation và feature entry points. Truy vết state từ nhánh cấp quyền đến từng gate; kiểm tra observer/cache và cập nhật màn hình đang mở.
  - Các bước:
    1. Lập danh sách premium features và mọi gate từ màn hình, navigation và feature entry points.
    2. Truy vết state từ nhánh cấp quyền đến từng gate; kiểm tra observer/cache và cập nhật màn hình đang mở.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Tất cả premium feature gates trong phạm vi tham chiếu đúng nguồn entitlement và cập nhật khi state thay đổi; không còn gate giữ state cũ sau nhánh mua hợp lệ trong code.
  - Nhánh lỗi/ngoại lệ: State stale, chỉ mở màn hình hiện tại, sản phẩm chưa đủ điều kiện premium.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Home observe premium state mới nhưng editor dùng giá trị cache không cập nhật là nhánh cần đánh giá từ code.

- [ ] **DEV-047 — Ads Logic** (dòng 60 trong sheet)
  - Nội dung gốc: Premium user phải ẩn toàn bộ ads
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 60 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có premium và ads, theo yêu cầu premium tắt toàn bộ ads.
  - Tiền điều kiện: Có premium state và source của mọi ad entry point đang dùng trong app.
  - Tiêu chí kiểm chứng từ source: Liệt kê toàn bộ ad entry points, gồm lifecycle callbacks và view đã được gắn trước khi premium thay đổi. Truy vết gate trước load/show, callback muộn và xử lý ad view/cache khi entitlement đổi.
  - Các bước:
    1. Liệt kê toàn bộ ad entry points, gồm lifecycle callbacks và view đã được gắn trước khi premium thay đổi.
    2. Truy vết gate trước load/show, callback muộn và xử lý ad view/cache khi entitlement đổi.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Mọi điểm load/show Banner, Native, Inter, Open và Reward đang dùng đều xử lý premium theo rule; ad cache và callback đến sau nâng cấp không bỏ qua gate hoặc giữ ad view sai.
  - Nhánh lỗi/ngoại lệ: Ads đã cache, lifecycle show trễ, native/banner vẫn bám view cũ.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Interstitial có gate nhưng App Open show trong onStart không kiểm tra premium là lỗi source cần dẫn riêng.

- [ ] **DEV-048 — Non-Premium Logic** (dòng 61 trong sheet)
  - Nội dung gốc: User thường phải vẫn thấy ads
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 61 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có ads cho user thường theo requirement.
  - Tiền điều kiện: Có non-premium state, ads entry points và consent/config defaults trong source.
  - Tiêu chí kiểm chứng từ source: Truy vết nhánh non-premium từ state khởi tạo/refresh tới từng ads entry point. Đọc điều kiện consent/config/lifecycle và xử lý load error; tìm cờ premium cũ hoặc return sớm khiến ads bị disable sai.
  - Các bước:
    1. Truy vết nhánh non-premium từ state khởi tạo/refresh tới từng ads entry point.
    2. Đọc điều kiện consent/config/lifecycle và xử lý load error; tìm cờ premium cũ hoặc return sớm khiến ads bị disable sai.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: User thường có đường request/show ads khi thỏa điều kiện trong code; premium state cũ không tắt nhầm ads, consent/config/no-fill được xử lý riêng với entitlement. Không yêu cầu network có fill.
  - Nhánh lỗi/ngoại lệ: Premium state cũ không reset, remote config tắt ads, consent chưa đáp ứng.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Nhánh request ads đúng nhưng network chưa trả quảng cáo không phải FAIL của kiểm tra source.

- [ ] **DEV-049 — Trial Expiry** (dòng 62 trong sheet)
  - Nội dung gốc: Với gói sub trial, hết trial vào app lại phải restore state đúng
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 62 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có subscription trial và logic entitlement khi hết hạn.
  - Tiền điều kiện: Có source refresh/query entitlement, product/offer mapping và trạng thái trial/expiry truy cập được.
  - Tiêu chí kiểm chứng từ source: Truy vết startup/resume đến query/refresh entitlement và nơi cập nhật premium state. Đọc nhánh active sau trial, expired, cache và query error; đối chiếu gate tính năng/ads sau mỗi state.
  - Các bước:
    1. Truy vết startup/resume đến query/refresh entitlement và nơi cập nhật premium state.
    2. Đọc nhánh active sau trial, expired, cache và query error; đối chiếu gate tính năng/ads sau mỗi state.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Khi refresh trả entitlement expired, code cập nhật khóa premium và ads đúng rule; trial chuyển sang gói trả phí còn hiệu lực không bị coi là expired; lỗi query không dùng state sai ngoài chủ đích.
  - Nhánh lỗi/ngoại lệ: Trial tự gia hạn thành subscription còn hiệu lực, response lỗi, dữ liệu cache.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Không yêu cầu chờ trial kết thúc thật; đọc cách code xử lý active và expired. Chưa rõ app có trial thì nêu đầu vào source/config còn thiếu.

- [ ] **DEV-050 — Subscription Info** (dòng 63 trong sheet)
  - Nội dung gốc: Tên loại gói + Giá hiển thị ở paywall phải khớp dialog Google
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 63 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có paywall subscription.
  - Tiền điều kiện: Có code lấy ProductDetails/offer và mapping tên, chu kỳ, currency, giá cùng offer token của paywall.
  - Tiêu chí kiểm chứng từ source: Truy vết ProductDetails/pricing phases tới text paywall và offer được chọn. Đối chiếu product ID, offer token, chu kỳ, currency và công thức giá với tham số Billing; đọc nhánh đổi offer/locale.
  - Các bước:
    1. Truy vết ProductDetails/pricing phases tới text paywall và offer được chọn.
    2. Đối chiếu product ID, offer token, chu kỳ, currency và công thức giá với tham số Billing; đọc nhánh đổi offer/locale.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Paywall dùng đúng dữ liệu product/offer tương ứng với tham số mở Billing; tên gói, chu kỳ, currency và công thức quy đổi nhất quán, không hardcode giá/chu kỳ trái mapping.
  - Nhánh lỗi/ngoại lệ: Locale/currency khác, nhiều offer/trial phase, offer thay đổi sau khi tải UI.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Paywall chọn offer A nhưng mở Billing bằng token B là sai mapping có thể xác định từ source.

- [ ] **DEV-051 — Coin Purchase** (dòng 64 trong sheet)
  - Nội dung gốc: Mua coin thành công cộng đúng số lượng
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 64 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có sản phẩm mua coin.
  - Tiền điều kiện: Có product-to-coin mapping, quantity và code cập nhật số dư.
  - Tiêu chí kiểm chứng từ source: Truy vết product ID/quantity qua nhánh purchase hợp lệ đến thao tác ghi số dư. Đối chiếu bảng mapping, xử lý quantity và idempotency của callback theo flow.
  - Các bước:
    1. Truy vết product ID/quantity qua nhánh purchase hợp lệ đến thao tác ghi số dư.
    2. Đối chiếu bảng mapping, xử lý quantity và idempotency của callback theo flow.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Nhánh mua coin hợp lệ cộng đúng mapping package và quantity được hỗ trợ (>=1); quantity không hợp lệ và callback lặp không làm số dư sai.
  - Nhánh lỗi/ngoại lệ: Quantity không hợp lệ, mapping sai SKU/product ID, callback bị xử lý lại.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Gói 100 coin tham chiếu mapping 10 coin là lỗi source khi cấu hình sản phẩm xác định được số lượng chuẩn.

- [ ] **DEV-052 — Multi Coin Buy** (dòng 65 trong sheet)
  - Nội dung gốc: Coin pack có thể mua nhiều lần
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 65 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có coin pack được thiết kế mua nhiều lần.
  - Tiền điều kiện: Có source xử lý consumable/consume và trạng thái nút mua coin pack.
  - Tiêu chí kiểm chứng từ source: Truy vết purchase hợp lệ đến consume/finalize và cập nhật trạng thái sở hữu/nút mua. Đọc nhánh consume lỗi, pending và retry; kiểm tra điều kiện mở lần mua kế tiếp theo product type.
  - Các bước:
    1. Truy vết purchase hợp lệ đến consume/finalize và cập nhật trạng thái sở hữu/nút mua.
    2. Đọc nhánh consume lỗi, pending và retry; kiểm tra điều kiện mở lần mua kế tiếp theo product type.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Coin pack có đường consume/finalize phù hợp tích hợp để mua lại; cờ sở hữu/local state không khóa vĩnh viễn lần mua sau, lỗi consume có nhánh xử lý rõ.
  - Nhánh lỗi/ngoại lệ: Consume/finalize lỗi, purchase đang pending, retry khi backend chưa ghi nhận.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Một cờ purchased lưu vĩnh viễn khóa coin pack consumable là lỗi source; không cần mua lại thật.

- [ ] **DEV-053 — Coin + Ads** (dòng 66 trong sheet)
  - Nội dung gốc: Mua coin không được tắt ads
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 66 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có coin pack; việc mua coin không kèm quyền tắt ads theo rule gốc.
  - Tiền điều kiện: Có mapping coin product, premium/remove-ads entitlement và các cờ purchase dùng chung.
  - Tiêu chí kiểm chứng từ source: Lần theo coin product ID qua purchase/restore callbacks tới mọi cờ entitlement được ghi. Đối chiếu cờ purchase dùng chung với gate quảng cáo để tìm đường coin vô tình tắt ads.
  - Các bước:
    1. Lần theo coin product ID qua purchase/restore callbacks tới mọi cờ entitlement được ghi.
    2. Đối chiếu cờ purchase dùng chung với gate quảng cáo để tìm đường coin vô tình tắt ads.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Nhánh mua/restore coin chỉ cập nhật quyền lợi coin, không bật premium/remove-ads hoặc bypass ads gate khi sản phẩm không kèm quyền này.
  - Nhánh lỗi/ngoại lệ: Dùng một cờ isPurchased cho mọi sản phẩm, restore coin bật premium nhầm.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Mọi purchase đều đặt isPremium=true khiến coin pack tắt ads là lỗi logic có thể truy vết.

- [ ] **DEV-054 — Data Clear** (dòng 67 trong sheet)
  - Nội dung gốc: Xóa data app không làm mất premium entitlement
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 67 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có premium entitlement cần khôi phục sau xóa app data.
  - Tiền điều kiện: Có source startup/query/restore entitlement và đường xử lý local storage rỗng.
  - Tiêu chí kiểm chứng từ source: Truy vết startup khi SharedPreferences/database chưa có premium state tới query/restore. Đọc account mapping, nhánh restore chậm/error và gate trước/sau kết quả; kiểm tra quyền lợi không chỉ phụ thuộc cờ local.
  - Các bước:
    1. Truy vết startup khi SharedPreferences/database chưa có premium state tới query/restore.
    2. Đọc account mapping, nhánh restore chậm/error và gate trước/sau kết quả; kiểm tra quyền lợi không chỉ phụ thuộc cờ local.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Khi local state rỗng, code vẫn query/restore premium từ nguồn quyền lợi đúng account và phối hợp loading/error trước khi quyết định gate; áp dụng cho subscription/premium, không phụ thuộc có coin.
  - Nhánh lỗi/ngoại lệ: Local storage rỗng, mạng lỗi, Play account/app account không khớp.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: App có subscription nhưng không có coin vẫn áp dụng DEV-054; không cần xóa data thật để review đường state rỗng.

- [ ] **DEV-055 — Reinstall Restore** (dòng 68 trong sheet)
  - Nội dung gốc: Cài lại app vẫn nhận premium đang còn hạn
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 68 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có premium còn hạn cần khôi phục sau cài lại.
  - Tiền điều kiện: Có startup/onboarding routing và cơ chế restore/query entitlement trong source.
  - Tiêu chí kiểm chứng từ source: Truy vết đường khởi tạo storage mới tới onboarding, query entitlement và routing. Đọc thứ tự await/callback và nhánh account mismatch/error; kiểm tra routing không bỏ qua kết quả restore theo requirement.
  - Các bước:
    1. Truy vết đường khởi tạo storage mới tới onboarding, query entitlement và routing.
    2. Đọc thứ tự await/callback và nhánh account mismatch/error; kiểm tra routing không bỏ qua kết quả restore theo requirement.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Đường khởi tạo với local state mới phối hợp query premium còn hiệu lực với routing onboarding/paywall đúng điều kiện trong code; account khác và restore chậm/error có nhánh riêng.
  - Nhánh lỗi/ngoại lệ: Restore chậm, Play service chưa sẵn sàng, account khác.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Route paywall trước khi query entitlement hoàn tất là điểm cần đánh giá thứ tự code; không yêu cầu gỡ/cài app.

- [ ] **DEV-056 — Next Session** (dòng 69 trong sheet)
  - Nội dung gốc: Ở phiên tải app tiếp theo premium state phải pass đúng
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 69 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App có premium state qua các phiên khởi động.
  - Tiền điều kiện: Có startup/session state, entitlement refresh và source điều hướng paywall/onboarding.
  - Tiêu chí kiểm chứng từ source: Truy vết cold-start/session entry point qua cache, refresh và điều hướng. Kiểm tra thứ tự callback, state loading/error và điều kiện route khi cache hết hạn hoặc restore chậm.
  - Các bước:
    1. Truy vết cold-start/session entry point qua cache, refresh và điều hướng.
    2. Kiểm tra thứ tự callback, state loading/error và điều kiện route khi cache hết hạn hoặc restore chậm.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Code phối hợp loading/refresh/navigation trước khi quyết định paywall theo entitlement; không phát lệnh route sai chỉ vì giá trị non-premium mặc định trong khi đang restore.
  - Nhánh lỗi/ngoại lệ: Cold start, restore chậm, cache hết hạn hoặc lỗi mạng.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Default false mở paywall ngay trước callback restore true là nguy cơ điều hướng sai từ source; không xác nhận hiện tượng flash trên UI.

- [ ] **DEV-057 — Google Play Billing** (dòng 70 trong sheet)
  - Nội dung gốc: Kiểm thử quá trình tích hợp Thư viện Google Play Billing
  - Nguồn/phiên bản: Tab `Dev checklist`, dòng 70 trong sheet nguồn đã trích xuất; trích xuất 22/10/2026.
  - Điều kiện áp dụng: App tích hợp Google Play Billing.
  - Tiền điều kiện: Có source Billing integration và tài liệu Billing chính thức truy cập được.
  - Tiêu chí kiểm chứng từ source: Truy vết kết nối Billing, query sản phẩm, launch parameters và purchase callbacks đến cấp quyền/finalize. Đối chiếu nhánh disconnected, pending, canceled, error, duplicate và restore với [tài liệu Billing](https://developer.android.com/google/play/billing/test); chỉ đánh giá đường code tương ứng.
  - Các bước:
    1. Truy vết kết nối Billing, query sản phẩm, launch parameters và purchase callbacks đến cấp quyền/finalize.
    2. Đối chiếu nhánh disconnected, pending, canceled, error, duplicate và restore với [tài liệu Billing](https://developer.android.com/google/play/billing/test); chỉ đánh giá đường code tương ứng.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Code xử lý kết nối, purchase states, validation/cấp quyền, acknowledgement/consume và query/restore phù hợp product type và tài liệu chính thức; pending/cancel/error/callback lặp không được xử lý như giao dịch hoàn tất.
  - Nhánh lỗi/ngoại lệ: Service disconnected, pending, canceled, truy vấn thất bại hoặc callback trùng.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Local unit test callback có thể bổ sung bằng chứng cho nhánh source; không tạo testcase giao dịch Play thực tế.

## 6. Build / SDK / Bảo mật / Quy ước code

Nguồn: yêu cầu bổ sung của người dùng ngày 22/10/2026. Đây là rule riêng của dự án; khi kiểm tra chính sách Google Play phải đối chiếu tài liệu chính thức tại thời điểm kiểm tra.

- [ ] **DEV-060 — Tương thích 16 KB page size**
  - Nội dung gốc: App phải được cập nhật để tương thích với thiết bị Android sử dụng memory page size 16 KB.
  - Nguồn/phiên bản: Yêu cầu bổ sung của người dùng ngày 22/10/2026; rule riêng của dự án.
  - Điều kiện áp dụng: Cấu hình variant release và native code/dependencies liên quan yêu cầu 16 KB; phạm vi chỉ source/config.
  - Tiền điều kiện: Có Gradle/NDK/CMake nếu dùng, dependency configuration, native source và metadata/tài liệu SDK truy cập được.
  - Tiêu chí kiểm chứng từ source: Đọc phiên bản AGP/NDK, build flags, CMake và dependency metadata/tài liệu SDK; liệt kê các đường đưa native code vào app xác định được. Tìm và đọc ngữ cảnh hằng page size, mmap/alignment assumptions trong native source; đối chiếu cấu hình với hướng dẫn chính thức và ghi SDK binary không có source.
  - Các bước:
    1. Đọc phiên bản AGP/NDK, build flags, CMake và dependency metadata/tài liệu SDK; liệt kê các đường đưa native code vào app xác định được.
    2. Tìm và đọc ngữ cảnh hằng page size, mmap/alignment assumptions trong native source; đối chiếu cấu hình với hướng dẫn chính thức và ghi SDK binary không có source.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Toolchain/config được đối chiếu hướng dẫn 16 KB chính thức; native source đã review không giả định cố định page size 4096; SDK có thể đưa native code vào được liệt kê cùng giới hạn source. Kết luận chỉ về cấu hình/code, không xác nhận tương thích binary.
  - Nhánh lỗi/ngoại lệ: SDK có native code nhưng không cung cấp source, giả định 4096, config khác nhau theo variant.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Tham chiếu: [Support 16 KB page sizes](https://developer.android.com/guide/practices/page-sizes).
  - Ví dụ minh họa: Không có native source tự viết chưa chứng minh dependency không dùng native code; ghi giới hạn này, không tạo case APK/AAB hoặc thiết bị.

- [ ] **DEV-061 — Google Play Billing Library ≥ 9**
  - Nội dung gốc: Google Play Billing Library phải dùng phiên bản major từ 9 trở lên.
  - Nguồn/phiên bản: Yêu cầu bổ sung của người dùng ngày 22/10/2026; rule riêng của dự án.
  - Điều kiện áp dụng: App tích hợp Google Play Billing/IAP/subscription.
  - Tiền điều kiện: Có Gradle/catalog, constraints/resolution rules và dependency graph release nếu có.
  - Tiêu chí kiểm chứng từ source: Truy vết billing/billing-ktx trực tiếp hoặc bắc cầu qua catalog, constraints và resolution rules. Đối chiếu version có hiệu lực với ngưỡng major >= 9 của dự án; dùng graph release nếu có, không lấy version debug thay release.
  - Các bước:
    1. Truy vết billing/billing-ktx trực tiếp hoặc bắc cầu qua catalog, constraints và resolution rules.
    2. Đối chiếu version có hiệu lực với ngưỡng major >= 9 của dự án; dùng graph release nếu có, không lấy version debug thay release.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Version Billing có hiệu lực trong dependency configuration của release có major >= 9; dùng version resolve khi có graph, nếu constraints/override không xác định được thì ghi đầu vào còn thiếu.
  - Nhánh lỗi/ngoại lệ: Version khai báo khác resolve, wrapper SDK kéo Billing bắc cầu, thiếu dependency report.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Catalog ghi major 9 nhưng graph resolve major 8 thì FAIL; app không có Billing thì NOT_APPLICABLE có căn cứ.

- [ ] **DEV-062 — SDK trong Gradle app ≥ 36**
  - Nội dung gốc: `compileSdk` và `targetSdk` của app đều phải ≥ 36. Đây là cách cụ thể hóa yêu cầu “SDK ≥ 36”; không áp dụng ngưỡng này cho `minSdk`.
  - Nguồn/phiên bản: Yêu cầu bổ sung của người dùng ngày 22/10/2026; rule riêng của dự án.
  - Điều kiện áp dụng: Mỗi variant release app cần phát hành theo rule SDK riêng của dự án.
  - Tiền điều kiện: Có module app, convention plugins, flavor/catalog và cấu hình override trong source.
  - Tiêu chí kiểm chứng từ source: Truy vết compileSdk/targetSdk từ module app qua catalog, convention plugin và flavor. Đọc override/CI configuration có trong repository và tính giá trị hiệu lực; dẫn đầy đủ nguồn giá trị, không yêu cầu manifest từ APK/AAB.
  - Các bước:
    1. Truy vết compileSdk/targetSdk từ module app qua catalog, convention plugin và flavor.
    2. Đọc override/CI configuration có trong repository và tính giá trị hiệu lực; dẫn đầy đủ nguồn giá trị, không yêu cầu manifest từ APK/AAB.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Giá trị compileSdk và targetSdk có hiệu lực trong cấu hình của từng variant release cần đánh giá đều >= 36; không áp dụng ngưỡng cho minSdk.
  - Nhánh lỗi/ngoại lệ: Flavor/CI override target SDK, convention plugin khác cấu hình nhìn thấy ở app.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: compileSdk=36, targetSdk=35 không đạt rule dự án; không cần dựng artifact để kết luận cấu hình này.

- [ ] **DEV-063 — Rà soát permission nguy hiểm và quyền cần Google xét duyệt**
  - Nội dung gốc: Kiểm tra các permission trong Manifest để xác định quyền nguy hiểm, nhạy cảm hoặc bị Google Play hạn chế và những quyền cần khai báo/xét duyệt.
  - Nguồn/phiên bản: Yêu cầu bổ sung của người dùng ngày 22/10/2026; rule riêng của dự án.
  - Điều kiện áp dụng: Permissions trong manifest/source theo variant và code sử dụng quyền; gồm quyền SDK xác định được từ tài liệu/source truy cập được.
  - Tiền điều kiện: Có manifest nguồn theo variant, manifest thư viện/source truy cập được, code dùng quyền và policy chính thức.
  - Tiêu chí kiểm chứng từ source: Đọc manifest main/flavor và manifest SDK/source có thể truy cập; đối chiếu từng quyền với tính năng và call sites, dùng merged manifest sẵn có nếu hữu ích. Truy vết check/request/result callbacks, nhánh denied/revoked và disclosure; đối chiếu yêu cầu chính thức cho từng quyền, không yêu cầu Console approval hoặc thao tác thiết bị.
  - Các bước:
    1. Đọc manifest main/flavor và manifest SDK/source có thể truy cập; đối chiếu từng quyền với tính năng và call sites, dùng merged manifest sẵn có nếu hữu ích.
    2. Truy vết check/request/result callbacks, nhánh denied/revoked và disclosure; đối chiếu yêu cầu chính thức cho từng quyền, không yêu cầu Console approval hoặc thao tác thiết bị.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Có inventory quyền và mục đích gắn với call sites; code kiểm tra/xin quyền, xử lý từ chối/thu hồi và disclosure phù hợp tiêu chí source áp dụng. Quyền thừa hoặc dùng sai mục đích có bằng chứng; yêu cầu khai báo/xét duyệt được nhận diện theo policy, không xác minh trạng thái Console.
  - Nhánh lỗi/ngoại lệ: Quyền thừa, quyền do SDK thêm, từ chối/thu hồi quyền, nhầm dangerous với quyền cần xét duyệt riêng.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Tham chiếu: [Declare permissions for your app](https://support.google.com/googleplay/android-developer/answer/9214102?hl=en), [Permissions and APIs that Access Sensitive Information](https://support.google.com/googleplay/android-developer/answer/16558241?hl=en).
  - Ví dụ minh họa: Nhánh denied vẫn gọi camera là lỗi source; chưa có ảnh prompt hoặc dữ liệu Console không chặn việc review callback.

- [ ] **DEV-064 — ProGuard/R8 và variant RELEASE**
  - Nội dung gốc: Có cấu hình ProGuard/R8 và app phải chạy được ở variant release với cấu hình đó được bật.
  - Nguồn/phiên bản: Yêu cầu bổ sung của người dùng ngày 22/10/2026; rule riêng của dự án.
  - Điều kiện áp dụng: Variant release phải bật ProGuard/R8 theo yêu cầu gốc.
  - Tiền điều kiện: Có release build configuration, proguardFiles/consumer rules và source dùng reflection, serialization hoặc JNI nếu có.
  - Tiêu chí kiểm chứng từ source: Đọc release/flavor overrides và proguardFiles để xác định rules thực sự được cấu hình nạp. Đối chiếu reflection, serialization, JNI và SDK call sites với keep/consumer rules; tìm rule không được nạp hoặc class bị bỏ sót.
  - Các bước:
    1. Đọc release/flavor overrides và proguardFiles để xác định rules thực sự được cấu hình nạp.
    2. Đối chiếu reflection, serialization, JNI và SDK call sites với keep/consumer rules; tìm rule không được nạp hoặc class bị bỏ sót.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Release bật minifyEnabled/isMinifyEnabled, nạp đúng file ProGuard/R8; các đường gọi gián tiếp xác định được từ source có keep rules/consumer rules phù hợp. Không kết luận build/cài/chạy release thành công.
  - Nhánh lỗi/ngoại lệ: Rule không được nạp, class chỉ được gọi bằng reflection, consumer rules từ SDK.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Tham chiếu: [Enable app optimization with R8](https://developer.android.com/topic/performance/app-optimization/enable-app-optimization).
  - Ví dụ minh họa: Có proguard-rules.pro nhưng release không tham chiếu file đó chưa đáp ứng cấu hình; không yêu cầu build log hoặc chạy bản minify.

- [ ] **DEV-065 — Không hardcode text hoặc chuỗi trong code sử dụng**
  - Nội dung gốc: Tuyệt đối không hardcode text cho `TextView`; phải khai báo string resources. Chuỗi dùng cho logic phải được khai báo constants và tham chiếu qua constants.
  - Nguồn/phiên bản: Yêu cầu bổ sung của người dùng ngày 22/10/2026; rule riêng của dự án.
  - Điều kiện áp dụng: Layout XML và Java/Kotlin có text cho TextView hoặc chuỗi dùng trong logic.
  - Tiền điều kiện: Có layout XML, resources, Java/Kotlin và constants của module/variant trong phạm vi.
  - Tiêu chí kiểm chứng từ source: Rà android:text/android:hint, setText/.text, nội suy và chuỗi ghép; truy vết nguồn text tới resources. Rà literal dùng trong logic, so sánh và callback; kiểm tra constants cùng các nơi tham chiếu, đối chiếu lint nếu đã chạy.
  - Các bước:
    1. Rà android:text/android:hint, setText/.text, nội suy và chuỗi ghép; truy vết nguồn text tới resources.
    2. Rà literal dùng trong logic, so sánh và callback; kiểm tra constants cùng các nơi tham chiếu, đối chiếu lint nếu đã chạy.
    3. Ghi actual, status và bằng chứng cho tiêu chí source; nếu thiếu đầu vào thì nêu đúng blocker, nếu không áp dụng thì dẫn căn cứ.
  - Kết quả mong đợi: Text hiển thị cho TextView lấy từ string resources, placeholder/plurals khi phù hợp; string dùng trong logic tham chiếu constants có tên, không dùng UI constants thay resources.
  - Nhánh lỗi/ngoại lệ: Nội suy chuỗi, placeholder/plurals, literal lọt trong callback hoặc so sánh logic.
  - Bằng chứng cần thu: File:line, call chain, resources/config/dependency và nguồn đối chiếu liên quan; lệnh cùng exit code của lint/local unit test nếu đã chạy.
  - Ví dụ minh họa: Thay title.text = "Welcome" bằng getString(R.string.welcome); dùng STATUS_READY thay literal "ready" ngoài nơi khai báo constant.

## Ví dụ minh họa — chưa phải rule được xác nhận

- Nội dung gốc: Khi từ chối quyền camera, app không crash và cho phép thử lại.
- Điều kiện áp dụng: Source có tính năng camera và code xin quyền.
- Tiền điều kiện: Đọc được permission callbacks và entry points camera.
- Các bước: Truy vết check/request permission, nhánh denied và action thử lại; đọc mọi đường mở camera từ callback.
- Kết quả mong đợi trong source: Nhánh denied không mở camera, có state/thông báo phù hợp và có đường thử lại theo trạng thái quyền.
- Bằng chứng: File:line của permission callback, điều kiện mở camera và action thử lại; local unit test nếu đã chạy.

Ví dụ chỉ đánh giá xử lý từ chối trong code; không xác nhận app không crash trên thiết bị và không tự chứng minh toàn bộ Permissions policy.
