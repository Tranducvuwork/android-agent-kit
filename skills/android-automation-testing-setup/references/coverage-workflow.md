# Coverage toàn app và tổ chức test

Áp dụng cho project Android XML/Views bất kỳ. Phát hiện package/framework từ app;
không dùng tên app, module, đường dẫn, dependency hoặc nghiệp vụ ví dụ làm mặc định.
Đọc cùng [workflow báo cáo](automation-reporting-workflow.md).

## 1. Bảo vệ production trước khi làm việc

- Chỉ ghi mã test vào source set test hiện có, thông thường `src/test/`,
  `src/androidTest/`, `src/testFixtures/`, và helper/fixture test. Report/evidence
  nằm trong `autotesting-reports/`. Giữ thay đổi sẵn có của người dùng.
- Cho phép cấu hình test tối thiểu: test dependency, runner, test options. Ghi diff,
  đường dẫn và lý do; rà soát diff để xác nhận không đổi dependency runtime,
  version build stack, applicationId, signing, min/target SDK hay release settings.
- Không sửa source production, resource, manifest production, interface/DI hoặc bug.
  Không sửa `src/debug` để lách giới hạn. Custom Application, DI override và fake
  phải thuộc test. Nếu cần production seam, ghi BLOCKED và điều kiện tiếp tục.
- Chụp snapshot bằng production guard trước khi thêm test và sau khi thực thi. Execution gate v2 tự kiểm tra live source so với snapshot, không cần gọi check riêng để hoàn tất.
  Guard bảo vệ cả nội dung đang dirty và phát hiện file production mới/xóa/đổi.
  Guard không thay thế việc review diff cấu hình Gradle hoặc custom source roots.
  Bổ sung hash thủ công cho production roots do build chỉ định ngoài `src/` nếu
  guard mặc định chưa bao gồm. Không dùng restore/reset để xóa thay đổi người dùng.

## 2. Discovery: dựng mẫu số coverage trước khi chọn case

1. Ghi source ref/branch, thay đổi đang có, skill path/version, app/module/variant,
   framework, supported devices/configurations. Source không thuộc Git dùng hash
   snapshot làm ref. Nếu test/report nằm ở branch khác, báo rõ và giữ source đã chọn.
2. Đọc yêu cầu/tài liệu và source của variant: manifest entrypoints, package,
   Activity/Fragment/dialog, layout/menu/adapter và click handler, ViewModel/state,
   repository/DAO/migration, network, receiver/service/worker và liên kết điều hướng.
   Module app là điểm vào; theo dependencies có hành vi phục vụ app.
3. Lập catalog package với source refs và disposition. DTO/constants không cần test
   hình thức; liên kết tới hành vi sử dụng chúng hoặc ghi lý do không áp dụng.
4. Lập workflow gồm màn hình, hành động, dữ liệu, tác động nền, điểm vào/kết thúc,
   source refs và loại `screen`, `multi_screen`, `cross_package` hoặc `long`.
5. Với mỗi workflow, liệt kê obligation: thành công, loading/empty/error, validation,
   input class/boundary, cancel/back/retry, permission, persistence, recreation và
   state restoration khi áp dụng. Xem thêm thời gian/timezone, offline, feature flag,
   notification/deep link, locale/font/theme/window size theo hành vi app hỗ trợ.
   Chọn cấu hình đại diện có lý do, tránh tích Descartes không có giá trị kiểm chứng.
6. Expected dựa trên yêu cầu/hợp đồng độc lập và kết quả quan sát được. Khi code và
   yêu cầu mâu thuẫn hoặc thiếu expected, ghi câu hỏi/gap; không sao chép bug vào
   expected. Obligation vẫn tồn tại dù chưa triển khai/chưa chạy được.
7. Đối chiếu lần hai: mọi entrypoint và hành vi đã tìm thấy phải được ánh xạ hoặc
   có lý do không áp dụng. Khảo sát runtime khi có môi trường và phạm vi cho phép,
   bổ sung workflow bị bỏ sót trước khi khóa baseline. Discovery chưa đủ thì giữ
   `discovery_complete: false`; không tuyên bố full coverage.

TEST mặc định là `full_app` trên variant đã chọn. Chỉ dùng `focused` khi người dùng
giới hạn rõ chức năng/phạm vi. Ngân sách/thời gian, test khó viết, thiếu thiết bị hay
lỗi app không phải lý do loại case khỏi inventory. Feature không hoạt động ở variant
hiện tại được giải thích trong exclusions; UI ngoài phạm vi Views là gap, không
được coi không áp dụng để tuyên bố full-app. Không cần số testcase tối thiểu cố định.

## 3. Test theo package và workflow

- Component/unit/DAO/single-screen UI test mirror package production dưới source
  set thích hợp. Tên lớp mô tả đối tượng/hợp đồng, method mô tả hành vi kiểm chứng.
- Multi-screen, integration giữa hợp đồng nhiều package hoặc luồng nhiều giai đoạn
  tách vào `<base_package>.workflows.<feature>`: JVM ở `test`, thiết bị ở `androidTest`.
  Dependency được fake trong một component test không tự biến nó thành workflow.
- Workflow có ít nhất một scenario xuyên suốt xác minh kết quả chính; nhánh lỗi,
  hủy/khôi phục liên quan đường đi có scenario độc lập. Nhánh logic thuần có thể
  được kiểm chứng bằng unit case có mapping, thay vì lặp toàn bộ hành trình.
- Mỗi journey có checkpoints hành vi: action, expected, assertion, dữ liệu sau bước.
  Không dùng một test thiết lập state để test sau tiếp tục. Mỗi case chạy riêng được.
- Helper điều hướng, setup, fake và failure-evidence đặt trong package test hỗ trợ.
  Không giấu assertion quan trọng trong helper không có checkpoint rõ ràng.
- Mỗi `AT-xxx` có đúng một owner `package` hoặc `workflow`; ghi related packages,
  workflow IDs, screens và test symbol. Liên kết giữa nhóm không nhân bản case.
- Chọn unit/database/Espresso/UI Automator theo hành vi. Hướng dẫn E2E ít hành trình
  giá trị cao chỉ giới hạn hành trình dài xuyên nhiều tính năng; không thu hẹp danh
  mục workflow cần bao phủ bằng các lớp test phù hợp.

## 4. Triển khai và chạy toàn bộ inventory

Ưu tiên theo rủi ro để sắp thứ tự, không bỏ case ưu tiên thấp. Test khó triển khai
trong giới hạn production vẫn có định nghĩa và blocker. Tiếp tục nhóm độc lập khi
nhóm khác fail/crash hoặc thiếu hạ tầng. Test dependency mới chỉ dùng khi cần.

Fake/in-memory fixture kiểm chứng logic/UI có kiểm soát. UI hệ thống như permission
cần kiểm chứng thực tế bằng automation thiết bị khi khả dụng. Chạy tích hợp thật
hoặc sandbox khi có môi trường; ghi rõ `fake`, `sandbox` hoặc `real` trong report.
Runner vô hiệu hóa ads/billing/worker không cung cấp bằng chứng cho chức năng đó.
Giữ riêng mức xác minh tích hợp; không gọi fake PASS là xác minh dịch vụ thật.

Run mới dùng coverage v2; dùng collector record-test-run.py để chạy/thu raw JUnit XML hoặc instrumentation, lưu manifest/hash và mapping runner_result. RETEST v2 giữ nguyên baseline v1/v2 và thu evidence mới. Trước/sau mỗi case reset fixture phù hợp. Lưu selector, lệnh, thời gian, run/source,
environment, runner result và [ảnh lỗi](failure-evidence.md). Không đổi production,
expected, golden, bỏ assertion hoặc skip case để tạo kết quả đạt.

## 5. Báo cáo nhóm và điều kiện hoàn tất

- `report.md`: metadata, coverage design/implementation/execution, PASS/FAIL,
  integration verification, gaps, index nhóm và lịch sử baseline.
- `packages/<package-path>/report.md`: case owner package; package-path lấy từng
  segment package làm thư mục. `workflows/<workflow-id>/report.md`: journey cases,
  related packages/screens và checkpoints. Dùng [mẫu nhóm](../assets/templates/group-report-template.md).
- Mỗi case chỉ có một trang chi tiết chính; nhóm khác liên kết tới nó. Số liệu được
  tính từ ID duy nhất trong artifact, không cộng các liên kết tham khảo.
- Lỗi ghi actual/expected, testcase/checkpoint, log, ảnh hoặc lý do thiếu, source nghi
  vấn (phân biệt suy luận và bằng chứng). Không tự sửa lỗi.
- Tách ba gate: design (đủ mapping/expected), implementation (đủ automation),
  execution (mọi case có PASS/FAIL mới và production được bảo toàn). PASS toàn suite
  không xác nhận discovery đầy đủ. Gate failed không ngăn lưu report tiến độ.
- Dùng [định dạng coverage và validator](coverage-format.md). Validator xác nhận
  tính nhất quán dữ liệu, không chứng minh agent đã đọc hết source hoặc assertion đúng.

## 6. Baseline và tương thích

Chỉ khóa baseline sau khi discovery/định nghĩa đủ; bản draft còn có thể bổ sung case.
Baseline setup-only có thể hợp lệ với NOT_TESTED. Sau khi khóa, RETEST giữ nguyên
scope, package/workflow/obligation và định nghĩa case. Automation/mapping method mới
được ghi riêng khi tương đương expected gốc. Coverage mới tạo TEST/baseline mới có
liên kết baseline trước; giữ lịch sử cũ.

Mỗi run giữ artifact và báo cáo nhóm snapshot riêng. File TEST gốc chỉ cập nhật tiến
độ/index tới snapshot mới nhất và thêm lịch sử; trang nhóm TEST ban đầu và evidence
gốc giữ nguyên. Baseline Markdown cũ thiếu artifact vẫn RETEST theo inventory cũ;
ghi coverage toàn app là **chưa đánh giá**, không dựng mapping/expected để vượt gate.
