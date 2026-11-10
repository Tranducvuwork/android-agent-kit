# Automation TEST/RETEST: báo cáo và theo dõi tiến độ

Đọc tài liệu này cùng [coverage-workflow.md](coverage-workflow.md) trước khi phân tích, thiết lập hoặc chạy test. Trả lời và viết report bằng tiếng Việt trừ khi người dùng yêu cầu khác. Chỉ viết/chạy automation và cấu hình test tối thiểu, không sửa production trong TEST lẫn RETEST. Giữ đúng yêu cầu chỉ phân tích/thiết lập. Quy định bảo vệ production và coverage của extension ưu tiên hơn các đề xuất test seam/DI trong 12 bước gốc.

## 1. Project, chế độ và đường dẫn

- Resolve symlink để xác định `SKILL_DIR`. Đọc workflow và template từ gói skill đang cài, không từ repository nguồn hoặc một skill khác.
- `PROJECT_ROOT` là source root Android được chỉ định; đường dẫn tương đối tính từ working directory. Chỉ dùng working directory mặc định khi xác định được đó là project Android. Nếu chưa xác định được project, hỏi đường dẫn; không tự chọn project khác hoặc ghi report vào nơi cài skill.
- Đọc hướng dẫn repository app, xác định applicationId/app, module, variant, version, source ref/thay đổi chưa commit, framework, JDK/SDK, runner và thiết bị/emulator nếu có liên quan. Đọc task/cấu hình project trước khi chọn lệnh; không đoán một task cho mọi project.
- `TEST` dùng cho đợt đầu hoặc một inventory/bộ tiêu chí mới, là mặc định khi không có yêu cầu RETEST. `RETEST` dùng khi được yêu cầu kiểm tra lại, sau fix hoặc cập nhật kết quả sau sửa lỗi. Không tự chuyển RETEST thiếu baseline thành TEST; chế độ mặc định không mở rộng yêu cầu chỉ phân tích/thiết lập thành chạy test.
- Mỗi lần gọi phải tạo `PROJECT_ROOT/autotesting-reports/<run-id>/report.md`, kể cả chỉ phân tích/thiết lập, bị chặn hoặc chưa chạy xong. Khởi tạo report ngay khi xác định được project, rồi cập nhật trước khi kết thúc. Nếu chưa xác định được project hoặc không ghi được output, báo rõ chưa lưu và dữ liệu/quyền cần bổ sung.
- Run-id là `<yyyy-mm-dd>-<hhmmss>-<app>-<module>-<variant>-<test|retest>`. Lấy thời gian bắt đầu theo múi giờ phiên làm việc và ghi rõ múi giờ; app/module/variant viết thường, không dấu, phân cách bằng dấu gạch ngang. Thành phần chưa biết dùng `unknown` và giải thích; không chạy nhầm variant vì thiếu thông tin. Nếu tên thư mục đã tồn tại, lấy timestamp mới cho run trước khi tạo thư mục, không ghi đè hoặc thêm hậu tố ngoài format.
- Bằng chứng của từng run nằm trong `test-evidence/inputs/` (source state, inventory, baseline đã đọc), `test-evidence/checks/` (lệnh/log/kết quả runner), `test-evidence/screenshots/` khi có ảnh. Chỉ tạo phần có dữ liệu, giữ bản sao bằng chứng cần thiết của lần chạy để kết quả lần sau không ghi đè chúng.
- Dùng liên kết tương đối từ từng report tới baseline, report khác và bằng chứng. Tính lại đường dẫn khi dẫn bằng chứng từ report RETEST vào baseline; không sao chép nguyên đường dẫn tương đối giữa hai thư mục run khác nhau.
- Run mới dùng coverage v2, run.id khớp thư mục và có started_at/ended_at có timezone. RETEST lưu baseline {run_dir, sha256} theo coverage-format. Chụp snapshot production trước/sau; review diff mọi cấu hình test. Ghi skill path/version, branch/source thật và khác biệt test/report ở branch khác. Dùng [coverage-format.md](coverage-format.md) cho guard, artifact và validator Python 3.9+.
- Report đầu mối liên kết tới `packages/<package-path>/report.md` và `workflows/<workflow-id>/report.md`. Mỗi case chỉ có một owner/trang chi tiết chính; trang nhóm khác dùng liên kết tham khảo. Case count tính theo ID duy nhất trong artifact.

## 2. TEST: xác định inventory và baseline

Dùng [template TEST/baseline](../assets/templates/test-report-template.md).

- TEST mặc định `full_app` trên variant đã chọn. Khảo sát mọi package/workflow/nhánh áp dụng, rồi đối chiếu source trước khi chốt case. `focused` chỉ dùng khi người dùng giới hạn rõ; test hiện có là đầu vào, không phải mẫu số coverage. Đọc workflow coverage cho cách thiết kế và tách package/journey.
- Mỗi case có ID ổn định `AT-001`, `AT-002`, ...; owner, related packages/workflows/screens, layer, module/variant, mục tiêu, dữ liệu, test symbol/scenario hoặc ghi chưa triển khai, bước/checkpoints và expected độc lập. Phân biệt scenario/parameter có expected riêng; task Gradle không chứng minh mọi case đã chạy.
- Mọi hành vi áp dụng trong phạm vi phải có obligation và mapping. Khó triển khai, thiếu môi trường hay ít thời gian không phải lý do loại case. Expected chưa rõ giữ obligation/gap và discovery chưa hoàn tất. Tính năng không áp dụng có source/lý do ngoài case inventory; không dùng status thứ năm.
- Sau khi xác định được đầy đủ inventory, report TEST này trở thành baseline theo dõi tiến độ. Khóa ID, tên/mục tiêu, tiền điều kiện, bước và expected. Các phần này là định nghĩa gốc, không ghi đè bằng tiêu chí mới khi RETEST.
- Giữ riêng metadata và tổng hợp TEST ban đầu, inventory gốc, phần tiến độ hiện tại có thể cập nhật và lịch sử theo run. Lần TEST đầu, tiến độ hiện tại lấy kết quả TEST và lịch sử có mốc đầu tiên cho mọi case.
- Report chỉ phân tích/thiết lập vẫn có thể là baseline nếu inventory đã xác định đầy đủ; case chưa chạy dùng NOT_TESTED, không bịa kết quả. Nếu chưa xác định được inventory hoặc không có case trong phạm vi, ghi rõ điều đó, không coi report là baseline hợp lệ hay tuyên bố toàn bộ PASS.
- Baseline theo dõi testcase khác với reference image/golden của screenshot framework. Giữ workflow ảnh chuẩn hiện có; không cập nhật ảnh chuẩn, bỏ assertion, ignore test hoặc đổi expected chỉ để chuyển FAIL thành PASS.

## 3. Chạy test và kết luận từng case

Chỉ có bốn status, phản ánh lần chạy hiện tại:

- `PASS`: automation của case thực sự chạy hoàn tất, đạt toàn bộ assertion/expected và có bằng chứng mới phù hợp.
- `FAIL`: case đã thực sự chạy và có assertion thất bại hoặc lỗi thực thi của chính case; ghi expected, actual và bằng chứng lỗi.
- `BLOCKED`: thiếu đầu vào, môi trường, công cụ hoặc lỗi chuẩn bị khiến chưa thể chạy/kết luận; ghi phần đã làm, nguyên nhân cụ thể và điều kiện tiếp tục.
- `NOT_TESTED`: case chưa chạy hoặc chưa hoàn tất mà không có blocker cụ thể; ghi lý do và tiến độ thực tế.

Ghi riêng mức thực hiện `Có`, `Một phần`, `Chưa`: PASS/FAIL là Có; BLOCKED/NOT_TESTED là Một phần hoặc Chưa. Đọc source, thấy có test code, lời xác nhận đã fix hoặc exit code của task không đủ để ghi PASS cho từng case.

- Dùng record-test-run.py theo coverage-format cho mọi execution v2; thêm reference manifest/hash vào executions và runner_result vào từng completed attempt. Collector không tự sửa inventory/status. Thu lệnh thực sự chạy, thời gian bắt đầu/kết thúc, exit code, test selection, môi trường/module/variant và kết quả chi tiết theo case từ runner/log/XML/screenshot nếu framework có. Kiểm tra kết quả là của run hiện tại; không dùng file kết quả tồn dư hoặc kết quả cache/up-to-date mà không có bằng chứng chạy lại phù hợp.
- Dùng test selector hiện có để bao phủ đúng inventory; ghi rõ cách ánh xạ test method và scenario/parameter vào case ID. Nếu một task chạy thêm test ngoài inventory, dẫn kết quả đó riêng và không cộng vào số liệu baseline hoặc tạo ID mới trong RETEST. Unit tests độc lập vẫn tiếp tục nếu thiếu thiết bị chặn Espresso/instrumented tests.
- Lỗi build, dependency resolution, runner không khởi động hoặc thiếu thiết bị khi chưa có kết quả case là BLOCKED cho các case phụ thuộc, không FAIL hàng loạt. Case nào đã thực sự chạy có kết quả độc lập thì giữ kết quả đó.
- Test bị framework skip/ignore không được tính PASS: dùng BLOCKED nếu có điều kiện chặn cụ thể, hoặc NOT_TESTED nếu bị bỏ qua/chưa thực hiện mà không có blocker. Thiếu log để xác minh kết quả cần được nêu rõ; không đoán đạt từ việc lệnh kết thúc.
- Assertion thất bại, exception hoặc crash được runner gắn cho case đã thực thi là FAIL. Nếu chỉ biết hạ tầng làm gián đoạn mà không xác định được kết quả case, dùng BLOCKED cho case chưa kết luận.
- Nếu có retry, ghi mọi attempt và lý do; không xóa thất bại hoặc gọi case ổn định chỉ vì một attempt sau PASS. Chạy lại sau retry phải có bằng chứng mới và giữ lịch sử.
- Nếu có FAIL rồi retry PASS trong cùng run, kết quả case của run vẫn FAIL; ghi mọi attempt. Chạy RETEST ở run mới để có kết quả sau thay đổi của người dùng.
- Thu screenshot UI lỗi theo [failure-evidence.md](failure-evidence.md), ưu tiên trước teardown. Nếu thiếu ảnh, tối đa một attempt cùng fixture/config/source để lấy evidence. Gắn case/attempt/checkpoint/timing, log và ảnh thật; lỗi capture không che exception gốc. UI không chụp được cần lý do; unit không có UI ghi không áp dụng.
- Tách coverage design, implementation, execution và mức xác minh fake/sandbox/real. Validator chưa đạt không ngăn lưu tiến độ; không công bố full-app chỉ vì suite hiện có đều PASS.

## 4. RETEST: nạp và giữ nguyên baseline

Dùng [template RETEST](../assets/templates/retest-report-template.md). Report RETEST là snapshot của một lần chạy; baseline luôn là report TEST đầu tiên trong chuỗi.

- Đường dẫn baseline tương đối tính từ PROJECT_ROOT. Nếu người dùng đưa report RETEST, theo liên kết baseline chuẩn tới report TEST gốc và kiểm tra chuỗi; không biến report RETEST thành file tiến độ thay thế.
- Khi không có đường dẫn, tìm trong `PROJECT_ROOT/autotesting-reports/`, chỉ tự chọn khi có đúng một baseline hợp lệ cùng app/applicationId, module, variant và source project. Có nhiều đợt TEST phù hợp thì hỏi lựa chọn, không chọn chỉ bằng tên thư mục hoặc mtime. Commit khác do fix không tự làm baseline sai project.
- Kiểm tra baseline đọc được, inventory đầy đủ, ID duy nhất, các tiêu chí cần thiết và định danh project phù hợp. Sai project/variant, thiếu baseline, chuỗi không hợp lệ hoặc chưa xác định đầy đủ inventory thì ghi run RETEST bị chặn, không tạo inventory mới và không cập nhật baseline.
- Vẫn lưu report RETEST giải thích phần thiếu. Inventory chưa xác định phải ghi chưa xác định, không giả định bằng 0 case hoặc tự tạo một case BLOCKED. Nếu inventory đã xác định nhưng riêng một case thiếu bước/expected, giữ ID đó với BLOCKED, tiếp tục các case đủ dữ liệu; không tự bổ sung tiêu chí.
- Nạp metadata gốc, inventory, trạng thái gần nhất và toàn bộ lịch sử trước khi kiểm tra. Giữ bản đã đọc ở `test-evidence/inputs/baseline-before-update.md` nếu đọc được, để đối chiếu trạng thái trước và kiểm tra thay đổi trong lúc chạy.
- Chạy lại toàn bộ inventory, gồm PASS, FAIL, BLOCKED và NOT_TESTED; diff/fix chỉ ưu tiên thứ tự. Không thêm/bớt/tách/gộp/đánh lại ID hoặc đổi expected. Case mới, expected mới và thay đổi coverage ghi ở việc cần tiếp tục cho TEST/baseline mới.
- Kiểm tra lại blocker; dùng bằng chứng mới cho mọi case, không sao chép PASS hoặc actual cũ. Test method bị đổi tên chỉ được ánh xạ sang method/scenario mới khi chứng minh cùng case/expected, ghi mapping mới trong bằng chứng của run; không sửa định nghĩa gốc. Không tìm được mapping hoặc tính năng/tiêu chí baseline không còn áp dụng thì BLOCKED, nêu điều kiện tiếp tục hoặc nhu cầu TEST mới.
- Nếu người dùng chỉ yêu cầu phân tích/thiết lập hoặc dừng trước khi chạy hết, vẫn giữ mọi case trong inventory và ghi NOT_TESTED/BLOCKED lần này theo thực tế. Trạng thái cũ chỉ là lịch sử.
- Với baseline có coverage v1/v2, giữ scope/catalog/mapping và định nghĩa case, dùng validator với `--baseline`; run RETEST mới luôn dùng v2, ID/thư mục khác baseline và dùng execution mới do collector thu. Giữ nguyên artifact baseline v1; artifact/trang nhóm mỗi run là snapshot. Baseline Markdown legacy vẫn RETEST theo ID/expected cũ, ghi coverage toàn app chưa đánh giá; cần TEST mới để khảo sát rộng hơn, không tự dựng artifact cho baseline cũ.

## 5. Lưu report RETEST và cập nhật file TEST đầu tiên

1. Hoàn thiện snapshot kết quả lần này trong report RETEST: định danh run/source/môi trường, baseline chuẩn, toàn bộ ID/expected, status trước → lần này, actual, mức thực hiện, bằng chứng/lý do, tổng hợp và việc cần tiếp tục. Khởi tạo trạng thái cập nhật baseline là Chưa cập nhật.
2. Kiểm tra tập ID bằng đúng inventory baseline; không trùng/thiếu/thêm, tiêu chí gốc không đổi. Tổng PASS + FAIL + BLOCKED + NOT_TESTED bằng số case inventory. Tổng mức thực hiện cũng phải khớp. Số case đổi status dựa trên kết quả gần nhất trước run, không so mọi lần với TEST ban đầu.
3. Ngay trước khi ghi, đối chiếu baseline hiện tại với bản đã nạp. Nếu đã bị run khác sửa, dừng cập nhật baseline và ghi xung đột trong report; không ghi đè lịch sử mới.
4. Chuẩn bị bản baseline cập nhật: chỉ thay phần tiến độ hiện tại bằng toàn bộ kết quả lần này, ghi run/source/môi trường/report mới nhất, index tới trang nhóm snapshot mới nhất và thêm một mốc lịch sử cho mọi case. Giữ nguyên metadata/tổng hợp TEST ban đầu, inventory, artifact/trang nhóm TEST gốc, kết quả TEST ban đầu, mọi mốc RETEST cũ và bằng chứng. Không thay status cũ trong lịch sử bằng status mới.
5. Tính lại liên kết bằng chứng theo thư mục baseline; lưu qua file tạm cùng thư mục rồi thay thế sau khi kiểm tra đầy đủ. Nếu không ghi được, giữ baseline cũ và ghi rõ cập nhật chưa hoàn tất trong report RETEST.
6. Hoàn tất trường cập nhật baseline của report RETEST: Đã cập nhật, Chưa cập nhật hoặc Lỗi/xung đột kèm lý do thực tế. Có thể cập nhật report trong khi run đang diễn ra; sau khi kết thúc, giữ snapshot RETEST và bằng chứng của run đó. Chỉ file TEST gốc tiếp tục nhận tiến độ của run sau.

Không tạo `baseline.md` riêng, không ghi đè report RETEST trước và không sửa file báo cáo/ảnh chuẩn của framework để che lỗi. Nếu baseline đã cập nhật nhưng chưa lưu được trạng thái hoàn tất vào report RETEST, báo rõ cả hai kết quả ghi file; không tuyên bố mọi output đã đồng bộ.

## 6. Kiểm tra trước khi trả kết quả

- [ ] Report thực tế đã được lưu đúng project/run-id; không còn placeholder mẫu hoặc số liệu suy đoán.
- [ ] Mỗi case có một trong bốn status lần này và bằng chứng mới hoặc lý do chưa kết luận; các tổng khớp inventory.
- [ ] PASS/FAIL có bằng chứng thực thi đúng case, module/variant và run hiện tại.
- [ ] RETEST giữ nguyên tập ID và tiêu chí, giữ đủ lịch sử và liên kết tới report TEST gốc.
- [ ] Report RETEST và baseline ghi đúng tình trạng cập nhật; mọi bằng chứng dẫn từ mỗi file đều có đường dẫn đúng.
- [ ] Trang nhóm có đúng owner và liên kết; UI FAIL có ảnh đúng case/attempt/checkpoint hoặc lý do unavailable; kết quả không che FAIL trước retry.
- [ ] Production được execution gate tự kiểm tra live (checked_at/changed_paths), cấu hình được review test-only, thay đổi có sẵn của người dùng được bảo toàn.
- [ ] TEST/v2 RETEST chỉ ghi hoàn tất kiểm thử khi discovery đầy đủ, mọi case đã triển khai và có PASS/FAIL mới, production được bảo toàn. Legacy RETEST chỉ xác nhận hoàn tất inventory cũ, không full-app. Hoàn tất vẫn có thể còn FAIL; không gọi đó là toàn bộ đạt.

Phản hồi cuối cung cấp link report lần này, baseline nếu hợp lệ, số PASS/FAIL/BLOCKED/NOT_TESTED, chuyển trạng thái đáng chú ý và việc cần tiếp tục. Nếu không ghi được output hoặc chưa xác định inventory, nói rõ phần chưa hoàn tất; không báo kết quả test hoặc tiến độ đã được lưu khi chưa thực hiện.
