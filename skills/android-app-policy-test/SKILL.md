---
name: android-app-policy-test
description: Kiểm tra mã nguồn Android app theo dev checklist đóng gói cùng skill và chính sách Google Play; hỗ trợ retest sau fix. Dùng khi được gọi để test, retest hoặc rà soát source trước phát hành.
disable-model-invocation: true
---

# Kiểm tra mã nguồn Android và Google Play policy

## Mục tiêu

Kiểm tra từng rule của người dùng và từng yêu cầu Google Play có thể đánh giá bằng source, resources, cấu hình và dependencies; ghi rõ bằng chứng và giới hạn kết luận. Không tạo case runtime, giao dịch thực tế, kiểm tra APK/AAB, binary alignment hoặc build/cài/chạy artifact. Trả lời bằng tiếng Việt trừ khi người dùng yêu cầu khác.

## Công cụ và đường dẫn dùng chung

- Codex: gọi `$android-app-policy-test ...`; chỉ gọi rõ tên, theo `agents/openai.yaml`.
- Claude Code: gọi `/android-app-policy-test ...` ở đầu tin nhắn; `disable-model-invocation: true` ngăn tự kích hoạt.
- `SKILL_DIR` là thư mục thật chứa `SKILL.md` đang được nạp; resolve symlink trước khi mở tài liệu tương đối. Mọi template và checklist nền phải đọc từ `SKILL_DIR`, không phụ thuộc repository GitHub gốc hay cách cài (project, global, symlink hoặc copy).
- `PROJECT_ROOT` là source root Android người dùng chỉ định; đường dẫn tương đối được hiểu từ working directory của phiên gọi skill. Nếu không truyền source, dùng working directory khi xác định được đó là project Android; nếu chưa rõ thì hỏi. Không suy ra PROJECT_ROOT bằng cách đi lên từ SKILL_DIR, vì skill có thể được cài global.
- Checklist nền là `SKILL_DIR/references/dev-checklist.md`; báo cáo được lưu dưới `PROJECT_ROOT/qa-reports/`, bằng chứng trong `test-evidence/` của từng lần chạy. Không ghi report vào thư mục skill, cache của installer hoặc home chỉ vì skill được cài ở đó. Nếu source không ghi được, yêu cầu đường dẫn report thay thế và báo rõ phần chưa lưu.
- Lint/local unit tests bổ sung bằng chứng cho tiêu chí source; không coi việc có test hoặc cấu hình test là bằng chứng đủ để đánh dấu policy case `PASS`.
- Dùng công cụ đọc/tìm kiếm/chạy lệnh sẵn có của host. Nếu host thiếu truy cập web, source hoặc lệnh cần thiết, ghi `BLOCKED` cho phần phụ thuộc; không bịa bằng chứng và không yêu cầu tool chỉ tồn tại ở host khác.
- Đọc hướng dẫn repository app đích (`AGENTS.md` và `CLAUDE.md` nếu có, theo host). Giữ nguyên chế độ TEST/RETEST, testcase ID và quy tắc báo cáo trên cả hai host.

## 0. Chọn chế độ trước khi kiểm tra

- `TEST`: kiểm tra ban đầu và lập danh sách testcase theo checklist/policy trong phạm vi.
- `RETEST`: khi người dùng nói retest, kiểm tra lại sau fix hoặc cập nhật status sau sửa lỗi. Bắt buộc đọc và thực hiện [retest-workflow.md](references/retest-workflow.md) trước khi kiểm tra source.
- Với `RETEST`, dùng report trước làm baseline và kiểm tra lại toàn bộ testcase source có sẵn, bất kể status cũ hoặc ảnh hưởng của fix. Giữ nguyên ID, mục tiêu, bước thực hiện và expected; không generate testcase mới, tạo case thay thế hoặc thiết kế lại danh sách từ checklist. Case runtime/artifact cũ chỉ dẫn ở phần lịch sử ngoài phạm vi, không tính vào inventory source. Không chuyển sang quy trình thiết kế testcase của TEST.
- Các mục bên dưới vẫn quy định phương pháp và chất lượng bằng chứng; phạm vi thực hiện và cập nhật báo cáo ở chế độ RETEST phải theo workflow riêng. Đọc checklist hiện hành để đối chiếu thay đổi; danh sách và tiêu chí testcase RETEST lấy từ baseline.

## 1. Xác định đầu vào

- Đọc hướng dẫn repository và bắt buộc đọc toàn bộ [references/dev-checklist.md](references/dev-checklist.md) tính từ SKILL_DIR ở mỗi lần chạy, kể cả khi người dùng không nhắc lại đường dẫn. Đây là bản nền đi kèm gói cài đặt, không cần clone repo gốc hoặc có checklist trong project Android.
- Nếu `PROJECT_ROOT/checklists/dev-checklist.md` tồn tại, đọc thêm để đối chiếu rule của project. Giữ ID trùng khi nội dung giống nhau, không tạo case lặp; nếu cùng ID khác yêu cầu, ghi xung đột và làm rõ cách áp dụng, không tự ghi đè bản nền. File rule do người dùng chỉ định cũng là nguồn bổ sung theo cùng nguyên tắc.
- Đây là checklist nền bắt buộc. Rule ở đường dẫn khác hoặc trong hội thoại là bổ sung, không thay thế checklist này trừ khi người dùng yêu cầu rõ việc thay đổi phạm vi.
- Nếu file thiếu, rỗng hoặc không đọc được, báo rõ đường dẫn và đánh dấu phần checklist là `BLOCKED`; không âm thầm thay bằng mẫu hay báo đã kiểm tra đầy đủ. Tiếp tục phần policy và rule bổ sung có đủ dữ liệu.
- Xác định source root, package/applicationId, module/variant, versionName/versionCode và commit nếu có. Ghi trạng thái thay đổi chưa commit ảnh hưởng kết luận.
- Xác định min/target SDK, thị trường, nhóm tuổi, tính năng, quảng cáo, thanh toán và cấu hình build/remote config liên quan nếu có dữ liệu.
- Hỏi gộp những đầu vào còn thiếu ảnh hưởng trực tiếp đến kiểm tra; tiếp tục các kiểm tra độc lập có đủ dữ liệu. Không tự chọn project không liên quan.
- Khi người dùng muốn thêm rule, dùng mẫu [user-rules-template.md](assets/templates/user-rules-template.md) để hướng dẫn nhập. Không coi ví dụ là rule được người dùng chấp thuận và không ghi đè checklist hiện có.
- Nếu chỉ có APK/AAB mà không có source, yêu cầu đường dẫn mã nguồn; không tự chuyển sang kiểm thử runtime hoặc dịch ngược.

## 2. Chuẩn hóa rule và phạm vi policy

- Với TEST, lập danh sách đầy đủ 32 rule hiện có trong `references/dev-checklist.md` và dùng expected whitebox hiện hành; với RETEST, giữ nguyên inventory source và expected baseline theo workflow retest, ghi riêng chênh lệch checklist. Giữ ID `DEV-xxx`, nhóm và truy xuất nguồn gốc; không lấy hành vi runtime trong nội dung gốc làm tiêu chí source. Đọc cả ghi chú, điều kiện cấp nhóm và mọi checkbox vì chúng không phải bằng chứng của lần chạy mới.
- Không đánh lại số để lấp khoảng trống ID; không khôi phục rule đã bị loại bỏ từ sheet gốc. Lấy file local hiện tại làm nguồn rule của lần chạy.
- Tôn trọng mục tùy chọn và điều kiện như “chỉ test phần này cho app có Ads”; không biến optional improvement thành lỗi bắt buộc. DEV-034/037 đã bị loại khỏi checklist vì phụ thuộc tài liệu Lutech riêng; không khôi phục chúng. Với rule bổ sung, chỉ nhận phần có tiêu chí source; phần chỉ cần runtime/artifact được mô tả ở giới hạn, không tạo case.
- Với TEST, chỉ tạo case source có mục tiêu/expected kiểm chứng được bằng code, resources, cấu hình hoặc dependencies. Ad Inspector kiểm tra đường tích hợp/config, Billing kiểm tra state/callback, restore kiểm tra đường khởi tạo/refresh; không sinh thêm case mở app, giao dịch, quan sát UI hoặc kiểm tra artifact. Với RETEST, thực hiện lại các case baseline, không áp dụng bước tạo case. Mỗi DEV ID trong phạm vi có kết quả hoặc lý do chưa có testcase baseline, gồm `NOT_APPLICABLE` khi có căn cứ tính năng không tồn tại.
- Giữ nguyên nội dung rule gốc; với TEST, gán ID ổn định `USR-001`, `USR-002`, ... nếu thiếu. Với RETEST, giữ mapping/ID baseline, ghi rule mới ở việc cần tiếp tục. Không đổi ID đã có.
- Với mỗi rule: ghi nguồn, điều kiện áp dụng, tiền điều kiện, các bước, kết quả mong đợi, phương pháp và bằng chứng cần thu.
- Làm rõ rule mơ hồ hoặc mâu thuẫn; không tự sửa yêu cầu để khiến app đạt. Khi rule nội bộ xung đột policy, ghi riêng kết quả hai bên và nêu xung đột.
- Mở [policy-reference.md](references/policy-reference.md), tra nguồn Google chính thức ở mỗi lần chạy cho các policy đang được kiểm tra. Với RETEST, xác minh điều khoản cho toàn bộ policy case trong baseline, không giới hạn theo fix và không mở thêm nhóm policy để tạo case. Đọc điều khoản đầy đủ và ngoại lệ; không chỉ dựa vào bản tóm tắt hoặc kết quả tìm kiếm.
- Với TEST, chỉ tạo policy case cho tiêu chí đánh giá được từ source; gán ID `GP-<NHOM>-001`, lưu URL, tên điều khoản, ngày truy cập/hiệu lực và lý do áp dụng. Với RETEST, giữ ID/expected baseline và ghi chênh lệch policy theo workflow riêng, không tạo case mới. Không tạo case tổng quát xác nhận Data safety, Console approval, store listing, backend retention hoặc trải nghiệm thực tế; ghi chúng ở giới hạn. Nếu thiếu thông tin quyết định applicability của một tiêu chí source, ghi `BLOCKED` và nêu rõ dữ liệu thiếu, không đoán ngoại lệ.
- Phân biệt quy định đang hiệu lực và thay đổi sắp tới theo ngày chạy, ngày phát hành dự kiến, quốc gia, loại app và chương trình tham gia. Không cố định target API hoặc deadline trong skill.
- Nếu không truy cập được policy hiện hành, vẫn làm phần kiểm thử độc lập; đánh dấu kết luận policy cần nguồn đó là `BLOCKED`. Nguồn cũ chỉ dùng tham khảo và phải ghi ngày.
- Danh mục tham chiếu là điểm bắt đầu. Với TEST, duyệt Policy Center để bổ sung nhóm liên quan và ghi lý do loại trừ; với RETEST, ghi nhóm/yêu cầu mới vào việc cần tiếp tục cho đợt TEST riêng, không bổ sung testcase. Không tuyên bố đã bao phủ mọi policy chỉ từ checklist mẫu.

## 3. Thiết kế và thực hiện kiểm thử

### Đọc mã nguồn và cấu hình

- Đọc cấu hình Gradle, manifest nguồn theo variant/thư viện và merged manifest sẵn có nếu hữu ích; kiểm tra permissions, exported components, target SDK và dependency/SDK. Không yêu cầu manifest trích từ APK/AAB.
- Đối chiếu đường đi dữ liệu, disclosure/consent, quảng cáo, billing, xóa tài khoản và privacy policy với tính năng thực tế và điều khoản áp dụng.
- Dùng `rg` để tìm điểm cần kiểm tra, sau đó đọc ngữ cảnh. Một chuỗi tìm thấy hoặc không tìm thấy không đủ chứng minh tuân thủ hay vi phạm.
- Đọc task dự án đã có; dùng `./gradlew tasks` khi cần thay vì đoán module. Có thể chạy lint, local unit tests hoặc task dependency/manifest phục vụ source nếu môi trường cho phép; kiểm tra task graph khi chưa rõ và không chọn task tạo APK/AAB (assemble/bundle/package ứng dụng), kiểm tra binary alignment hay chạy thiết bị. Kết quả biên dịch phục vụ local unit tests không phải case kiểm tra artifact. Android lint không thay thế đánh giá Google Play policy.
- Không cài dependency hay sửa code app chỉ để hoàn thành báo cáo nếu chưa nằm trong yêu cầu của người dùng.

### Truy vết hành vi trong source

- Với mỗi rule, lần theo entry point → điều kiện → hành động → xử lý lỗi. Kiểm tra callback bất đồng bộ và nhánh liên quan như từ chối quyền, retry, hủy, mất mạng, consent, lifecycle.
- Đọc các nhánh theo variant, region, remote config, trạng thái đăng nhập; ghi giá trị chưa xác định. Không giả định code tồn tại đồng nghĩa sẽ được thực thi, hoặc code không thấy đồng nghĩa tính năng không tồn tại.
- Kiểm tra dependency trực tiếp/bắc cầu và manifest do SDK thêm nếu có dữ liệu. SDK dạng binary hoặc logic server không thể xác minh chỉ bằng source ứng dụng.
- Dẫn đường dẫn và dòng code, chuỗi gọi hàm, cấu hình và kết quả lint/unit test thực sự chạy. Phân biệt lỗi source, nghi vấn cần xác minh và lỗi tooling.
- Đối chiếu đường dữ liệu, disclosure và consent thực hiện trong code với policy; không suy ra toàn bộ Data safety, Console hoặc backend practices. Phần ngoài source chỉ ghi giới hạn, không tạo case hoặc chặn case source bằng việc thiếu bằng chứng ngoài phạm vi.
- Tiếp tục kiểm tra mọi nhánh source/ảnh local đọc được. Chưa xem hết không tự là blocker; chỉ ghi `BLOCKED` khi có đầu vào/công cụ cụ thể thiếu cho tiêu chí source. Không dùng thiếu app đang chạy, APK, thiết bị hoặc tài khoản giao dịch để chặn case source.

## 4. Đánh giá từng test case

- `PASS`: đã thực hiện đầy đủ kiểm tra source của case, đạt expected whitebox và có bằng chứng phù hợp.
- `FAIL`: đã hoàn tất kiểm tra và có bằng chứng source trái expected; policy finding phải gắn điều khoản đang áp dụng. Nêu mức độ và cách truy vết lỗi.
- `BLOCKED`: thiếu đầu vào, quyền truy cập, nguồn policy hoặc công cụ cần thiết cho chính tiêu chí source; ghi phần đã làm và điều kiện tiếp tục.
- `NOT_TESTED`: case source chưa bắt đầu hoặc chưa hoàn tất mà không có blocker cụ thể; ghi lý do và mức thực hiện thực tế. Không dùng để bổ sung case runtime/artifact.
- `NOT_APPLICABLE`: có căn cứ điều kiện áp dụng không đúng với app; ghi căn cứ. Thiếu dữ liệu không phải lý do để dùng trạng thái này.

Nếu đã đọc đủ source và xác định thiếu triển khai/config bắt buộc thì `FAIL`, không dùng tiền điều kiện để che lỗi thành `BLOCKED`. `BLOCKED` chỉ dùng khi không thể xác định vì thiếu đầu vào/quyền đọc/nguồn/công cụ cần thiết. Xác định applicability từ feature entry points và cấu hình, không chỉ sự hiện diện của SDK dùng chung.

`PASS` chỉ xác nhận expected source đã ghi, không xác nhận hành vi runtime hoặc artifact. Chỉ kết luận rule đạt khi mọi tiêu chí source bắt buộc đã được xác minh; không yêu cầu bằng chứng ngoài phạm vi để kết luận rule whitebox. Mức độ lỗi (`critical`, `high`, `medium`, `low`) độc lập với trạng thái; giải thích theo tác động và độ chắc chắn của bằng chứng.

## 5. Báo cáo và kiểm tra lại

- Bắt buộc tạo một file báo cáo chính theo [test-report-template.md](assets/templates/test-report-template.md) cho mỗi lần chạy, kể cả khi còn case bị chặn hoặc chưa kiểm tra. Lưu tại `PROJECT_ROOT/qa-reports/<run-id>/report.md`; bằng chứng bổ trợ nằm ở `test-evidence/` cùng run. Không chỉ trả kết quả trong chat.
- Đặt run-id theo `<yyyy-mm-dd>-<hhmmss>-<app>-<module>-<variant>-<test|retest>`, ví dụ `2026-10-29-094940-peptide-app-release-test` hoặc `2026-10-29-143000-peptide-app-release-retest`. Thành phần cuối là chế độ viết thường; không nối thêm `-retest` lần nữa. Lấy ngày/giờ lúc bắt đầu run theo múi giờ phiên làm việc và ghi rõ múi giờ trong report. Chuẩn hóa app/module/variant thành tên chữ thường, không dấu, phân cách bằng dấu gạch ngang; lấy từ đầu vào/cấu hình đã xác định, dùng `unknown` cho thành phần chưa xác định và giải thích trong report. Nếu trùng run-id, thêm `-02`, `-03`, ... sau chế độ để không ghi đè lần chạy cũ.
- Chia bằng chứng trong `test-evidence/` thành `inputs/` (trạng thái source, snapshot checklist, inventory và đầu vào được cung cấp), `checks/` (kết quả lint/local unit tests/dependency report thực sự chạy), `manifests/` (manifest theo variant hoặc merged manifest đã thu được). Chỉ tạo thư mục/file khi có dữ liệu; dùng tên file chữ thường, phân cách bằng dấu gạch ngang như `source-state.txt`, `lint-vital-release.txt`, `release-runtime-classpath.txt`, `merged-release-manifest.xml`. Dẫn liên kết tương đối từ `report.md` tới bằng chứng.
- Khởi tạo báo cáo sau khi lập danh sách case và cập nhật kết quả trước khi kết thúc. Mỗi TEST/RETEST là một thư mục ngang hàng dưới `qa-reports/`; báo cáo retest dẫn liên kết tương đối tới baseline và bằng chứng lịch sử theo workflow retest.
- Với TEST, ghi một case cho mỗi yêu cầu source có thể kiểm chứng độc lập. Với RETEST, giữ nguyên toàn bộ inventory/ID/expected source baseline, kiểm tra lại tất cả case và không bổ sung case; dẫn case runtime/artifact cùng lịch sử ngoài phạm vi có sẵn ở mục riêng. Không loại case source đang có chỉ vì rule bị xóa. Mỗi rule/policy source trong phạm vi phải liên kết tới case hoặc có lý do chưa có testcase baseline; không sinh case để lấp khoảng trống khi RETEST.
- Trong cùng `report.md`, bắt buộc có mục “Danh sách testcase và trạng thái”: một mục cho mỗi case, gồm case ID, tên, rule/policy ID, phương pháp, mức thực hiện (`Có`, `Một phần`, `Chưa`), status và bằng chứng/lý do. Liệt kê cả case chưa chạy hoặc không áp dụng để người đọc thấy rõ đã kiểm tra những gì.
- Đọc và đối chiếu source có thể là thực hiện case, không bắt buộc chạy lệnh. Với status lần này, `PASS`/`FAIL` có mức thực hiện `Có`; `NOT_APPLICABLE` là `Chưa` vì không thực hiện tiêu chí sau khi xác định không áp dụng; `BLOCKED`/`NOT_TESTED` có thể là `Chưa` hoặc `Một phần` tùy bằng chứng. Với RETEST, mỗi case source baseline phải có kết quả lần này; không dùng “Không retest” hoặc PASS lịch sử để bỏ qua case. Không đồng nhất đã xem xét rule với đã test đạt.
- Thêm mục đối chiếu checklist: đường dẫn, phiên bản/hash nếu có, tổng số rule đọc được và kết quả cho từng ID `DEV-xxx` kèm case/bằng chứng hoặc lý do chưa xác minh. Đối chiếu danh sách ID trong báo cáo với file để không bỏ sót rule; không sửa checkbox trong file nguồn khi báo cáo.
- Trước khi hoàn tất, kiểm tra case ID không trùng và tổng hợp khớp chi tiết. Với RETEST, tập ID source phải bằng đúng baseline, không thêm/thiếu; số case trong phạm vi bằng toàn bộ inventory source baseline và mỗi case có status lần này. Tổng theo status lần này và mức thực hiện đều bằng số case trong phạm vi. Case legacy ngoài source chỉ được dẫn riêng, không tính trong các tổng này. Không để placeholder mẫu; dữ liệu chưa biết phải ghi rõ lý do.
- Báo số lượng theo từng trạng thái, findings ưu tiên cao, giới hạn phạm vi và dữ liệu còn thiếu. Không đính kèm token, thông tin cá nhân hoặc secret trong log/ảnh chia sẻ.
- Chỉ ghi kết quả lệnh thực sự chạy; cung cấp đường dẫn bằng chứng và trích dẫn policy gần kết luận liên quan. Phân biệt quan sát, suy luận và dữ liệu người dùng cung cấp.
- Sau sửa lỗi, áp dụng workflow RETEST, cập nhật status có bằng chứng mới và giữ lịch sử trước/sau. Không tự sửa app khi người dùng chỉ yêu cầu kiểm thử.
- Kết luận giới hạn ở các case đã kiểm tra; không cam kết Google Play sẽ duyệt app.
- Trong phản hồi cuối, cung cấp link trực tiếp đến `report.md` kèm số case theo status. Nếu không ghi được file do giới hạn môi trường, báo rõ việc tạo file chưa hoàn tất và nguyên nhân; không tuyên bố báo cáo đã được lưu.

## Ví dụ gọi skill trong Codex

```text
$android-app-policy-test Kiểm tra source ../my-app.
Luôn duyệt checklist đi kèm skill và rà policy Google Play; không sửa code.
```

```text
$android-app-policy-test Chỉ kiểm tra source ../my-app về quyền camera và User Data.
Chỉ lập case source và ghi giới hạn kết luận; không sửa code.
```

```text
$android-app-policy-test Retest sau fix, source ../my-app,
baseline qa-reports/<run-id-truoc>/report.md.
Kiểm tra lại toàn bộ testcase source trong baseline, giữ nguyên ID/expected;
không generate testcase mới, cập nhật status bằng bằng chứng lần này.
```

## Ví dụ gọi skill trong Claude Code

```text
/android-app-policy-test TEST source ../my-app, module app, variant release.
```

```text
/android-app-policy-test RETEST source ../my-app,
baseline qa-reports/<run-id-truoc>/report.md. Đã fix: <mô tả hoặc commit>.
```
