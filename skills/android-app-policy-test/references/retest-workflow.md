# Retest sau sửa lỗi

Workflow này chỉ dùng ở chế độ `RETEST`. Phương pháp chỉ kiểm tra source, resources, cấu hình, dependencies và lint/local unit tests được phép; không tạo case runtime, giao dịch, APK/AAB, binary alignment hoặc build/cài/chạy artifact.

Mỗi lần RETEST phải kiểm tra lại toàn bộ testcase source có sẵn trong baseline, bất kể status cũ hoặc mức ảnh hưởng của fix. Baseline là nguồn duy nhất của danh sách testcase; không generate testcase mới, không tạo case thay thế và không thiết kế lại case từ checklist/policy hiện hành.

## 1. Nạp baseline

- Đọc `report.md` người dùng chỉ định, gồm danh sách case, rule/policy mapping, expected/actual, status, bằng chứng và findings. Đường dẫn baseline tương đối tính từ PROJECT_ROOT; đường dẫn tuyệt đối giữ nguyên. Nếu baseline là một lần retest, tiếp nối inventory/status gần nhất và chuỗi lịch sử của lần đó.
- Khi không chỉ định report, tìm trong cả `PROJECT_ROOT/qa-reports/` và đường dẫn cũ `PROJECT_ROOT/reports/android/`, không tìm trong nơi cài skill. Chỉ tự chọn lần gần nhất có định danh app, module/variant và source phù hợp từ cả hai vị trí; dựa vào run metadata và chuỗi baseline, không chỉ mtime hoặc tên thư mục. Nếu có nhiều nhánh report hoặc chưa xác định được app/variant, hỏi lựa chọn baseline.
- Nếu không có report đọc được hoặc không xác định được đầy đủ inventory/ID, báo `RETEST BLOCKED` và yêu cầu baseline. Không âm thầm chuyển sang TEST hoặc dựng testcase/kết quả cũ giả. Vẫn lưu report giải thích vì sao chưa thể retest, ghi inventory chưa xác định thay vì tổng kết kiểm thử đã hoàn tất. Nếu inventory đầy đủ nhưng một case thiếu expected, bước thực hiện hoặc kết quả cũ cần thiết, giữ ID, ghi phần thiếu và đánh dấu case đó `BLOCKED`; tiếp tục các case đủ dữ liệu, không tự bổ sung tiêu chí.
- Ghi đường dẫn/hash baseline, run-id, định danh source cũ và source hiện tại. Giữ nguyên report và bằng chứng cũ, kể cả bản nằm trong `reports/android/` với thư mục `evidence/`; không di chuyển/đổi tên chúng khi tạo run mới. Báo cáo retest có liên kết tương đối ngược tới baseline.
- Phân loại theo mục tiêu/expected thực tế, không chỉ hậu tố ID: toàn bộ case đánh giá source được tiếp nối trong inventory, kể cả case không được retest ở run trước. Case runtime/artifact hoặc xác minh Console/backend chỉ được dẫn ở mục “Lịch sử ngoài phạm vi source”; không chạy lại và không chuyển chúng thành testcase source mới. Ghi ID, lý do ngoài phạm vi, status cũ và link baseline/bằng chứng, không tạo status lần này cho chúng. Không coi việc loại khỏi scope là đã sửa lỗi và không đóng finding cũ. Không khôi phục các case đã được lưu riêng ở lịch sử ngoài phạm vi của baseline.

## 2. Khóa danh sách testcase theo baseline

- Sao chép đầy đủ inventory source từ baseline, giữ nguyên ID, rule/policy mapping, mục tiêu, tiền điều kiện, bước thực hiện và expected. Đối chiếu tập ID trước khi bắt đầu: không thêm, tách, gộp, đánh lại số hoặc loại bỏ testcase source.
- Tất cả case source đều thuộc phạm vi lần này: `PASS`, `FAIL`, `BLOCKED`, `NOT_TESTED` và `NOT_APPLICABLE`. Status cũ, việc không bị fix ảnh hưởng hoặc chưa gỡ blocker không phải lý do bỏ chọn case. Các ID người dùng nhấn mạnh được ưu tiên thực hiện, không thu hẹp danh sách baseline.
- Đọc toàn bộ `SKILL_DIR/references/dev-checklist.md` hiện hành và rule bổ sung của project để đối chiếu thay đổi yêu cầu. Checklist/policy mới không phải nguồn để sinh testcase trong RETEST. Ghi yêu cầu mới hoặc khoảng trống coverage vào mục việc cần tiếp tục và đề xuất một đợt TEST riêng; không tự bắt đầu đợt đó.
- Ghi diff giữa source đã test và source hiện tại nếu xác định được, gồm thay đổi chưa commit; dùng commit/hash/patch hoặc bản source cũ đã ghi, không tự giả định `HEAD~1`. Diff/fix chỉ giúp giải thích thay đổi và ưu tiên thứ tự kiểm tra, không quyết định case nào được chạy.
- Nếu thiếu ref cũ hoặc thông tin fix, ghi giới hạn chưa xác minh được toàn bộ diff và vẫn kiểm tra tất cả case baseline có đủ dữ liệu. Không chặn toàn bộ RETEST chỉ vì không chọn được phạm vi theo fix.
- Với rule/expected thay đổi hoặc rule bị xóa, ghi chênh lệch nhưng không sửa expected, tạo ID mới hay đưa case source đang có trong inventory ra lịch sử để bỏ retest. Đánh giá lại applicability theo tiền điều kiện baseline và source hiện tại. Nếu không thể kết luận theo tiêu chí baseline vì yêu cầu đã thay đổi hoặc thiếu nguồn cần thiết, ghi `BLOCKED` cùng lý do; không tự đổi `FAIL` cũ thành `PASS`/`NOT_APPLICABLE`. Các case DEV-034/037 đã nằm trong lịch sử ngoài phạm vi của baseline tiếp tục được giữ nguyên ở đó.

## 3. Thực hiện kiểm tra lại

- Với từng case trong toàn bộ inventory source baseline, đọc lại tiêu chí/tiền điều kiện và thực hiện lại các bước/phương pháp đã ghi trên source hiện tại. Kiểm tra đường gây lỗi gốc và nhánh liên quan; việc nhìn thấy commit sửa lỗi hoặc lời xác nhận “đã fix” không đủ để đổi status. Không chỉ sao chép actual hoặc bằng chứng cũ cho case từng PASS.
- Chạy lại lint/local unit test liên quan nếu đó là bằng chứng cần thiết và môi trường cho phép. Đọc và đối chiếu source cũng là thực hiện case nếu đó là phương pháp đã xác định; không bịa kết quả chạy lệnh.
- Thu bằng chứng mới với file:line, source ref/thay đổi chưa commit, timestamp và kết quả lệnh nếu có. Bằng chứng cũ chỉ dùng đối chiếu trước/sau.
- Với mọi case policy trong baseline, xác minh điều khoản hiện hành liên quan; ghi riêng thay đổi policy so với baseline và xử lý chênh lệch theo mục 2. Không mở thêm nhóm policy hoặc sinh testcase mới.
- Case từng `BLOCKED` phải được kiểm tra lại điều kiện chặn; còn thiếu thì ghi `BLOCKED` lần này với lý do hiện tại. Case từng `NOT_APPLICABLE` phải xác minh lại applicability: còn không áp dụng thì ghi bằng chứng mới; đã áp dụng thì thực hiện tiêu chí baseline và kết luận theo kết quả mới.
- Không bổ sung case source, runtime/artifact hoặc case thay thế. Case ngoài source cũ vẫn dẫn nguyên trạng ở lịch sử ngoài phạm vi. Không chặn case source bằng thiếu APK, thiết bị hoặc tài khoản giao dịch.

## 4. Cập nhật status và findings

- Case đã kiểm tra lại: ghi status trước → status lần này, actual mới, bằng chứng mới, mức thực hiện và lý do thay đổi. Kết quả lần này cũng có thể giữ nguyên `FAIL` hoặc chuyển sang `BLOCKED`/`NOT_TESTED`; không mặc định retest sẽ đạt.
- Mọi case trong inventory source phải có status lần này thuộc năm trạng thái; không dùng nhãn “Không retest” để bỏ qua case. Giữ status/actual/bằng chứng cũ trong lịch sử riêng, không dùng chúng thay kết quả hiện tại. Nếu chưa thực hiện xong, ghi `BLOCKED` khi có blocker cụ thể hoặc `NOT_TESTED` khi chưa hoàn tất mà không có blocker, kèm mức thực hiện và lý do.
- `PASS` chỉ khi toàn bộ tiêu chí source của case được xác minh bằng bằng chứng mới. Thiếu đầu vào cho tiêu chí source là `BLOCKED`; chưa hoàn tất review mà không có blocker cụ thể là `NOT_TESTED`, mức thực hiện `Một phần` hoặc `Chưa`. Phần ngoài source không phải điều kiện để case source đạt.
- Chỉ đóng finding source khi mọi case source bắt buộc liên quan đã được kiểm tra lại và đạt trên source hiện tại. Finding có phần runtime/artifact hoặc bằng chứng ngoài source cũ vẫn giữ phần đó còn mở ở lịch sử; PASS source mới không đủ đóng toàn bộ finding. Nếu lần này bị chặn, giữ finding còn mở và bằng chứng cũ; lỗi vẫn tồn tại thì ghi còn lỗi, hồi quy từ `PASS` sang `FAIL` cần finding/bằng chứng mới.
- Cập nhật cả danh sách testcase, chi tiết case, đối chiếu rule, findings và số liệu tổng hợp theo kết quả lần này. Với rule gồm nhiều case, không chuyển cả rule thành PASS khi còn case bắt buộc chưa xác minh; kết quả lịch sử không chứng minh rule trên source mới.

## 5. Lưu báo cáo retest

- Dùng mẫu report chung; ghi chế độ `RETEST`, baseline, phạm vi fix và xác nhận phạm vi là toàn bộ inventory source baseline. Lưu tại `PROJECT_ROOT/qa-reports/<run-id>/report.md`. Run-id theo quy ước trong SKILL.md, đã có chế độ `retest` ở cuối (trước hậu tố chống trùng nếu có), ví dụ `2026-10-29-143000-peptide-app-release-retest`; không nối thêm `-retest`. Thư mục retest nằm ngang hàng với các run khác dưới `qa-reports/`, không lồng trong baseline.
- Bằng chứng mới nằm trong `test-evidence/inputs/`, `test-evidence/checks/`, `test-evidence/manifests/` theo loại dữ liệu; chỉ tạo phần có dữ liệu. Không ghi đè baseline hoặc ghi vào nơi cài skill.
- Report mới giữ nguyên tập testcase source baseline và ghi kết quả lần này cho từng case, kể cả case bị chặn hoặc chưa hoàn tất. Case legacy ngoài source và case đã được lưu riêng trong lịch sử baseline tiếp tục dẫn ở lịch sử ngoài phạm vi. Tính lại liên kết tương đối tới baseline và bằng chứng theo vị trí report mới, kể cả khi baseline dùng đường dẫn cũ; không thay hàng loạt `evidence/` lịch sử thành `test-evidence/`.
- Ghi lịch sử mỗi case: run/thời điểm, source ref, status trước, status lần này, status gần nhất, nguồn status và bằng chứng. Lần retest sau phải tiếp nối lịch sử này, không bỏ các lần trung gian.
- Đếm riêng trong inventory source: tổng case baseline, số case thuộc phạm vi retest, mức thực hiện, status lần này và số thay đổi status. Số case trong phạm vi bằng tổng inventory source baseline; số case mới và số case source bị loại khỏi inventory đều bằng 0. Không cộng PASS lịch sử vào số PASS mới; không cộng case legacy ngoài source vào inventory hoặc bất kỳ tổng status/mức thực hiện nào.
- Kiểm tra tập ID source trong report mới bằng đúng tập ID source baseline, không trùng/thiếu/thêm; mục tiêu, bước thực hiện và expected không đổi. Mọi ID baseline ngoài source có link/lý do ở lịch sử. Summary khớp chi tiết, status lịch sử không đổi, mọi status lần này có bằng chứng/lý do. Tổng năm status lần này và tổng mức thực hiện đều bằng tổng inventory source baseline.
- Chỉ báo hoàn tất retest toàn bộ khi không còn `BLOCKED`/`NOT_TESTED` và mọi case đã được kiểm tra lại hoặc xác minh không áp dụng bằng bằng chứng mới. Phản hồi cuối phải nói rõ đây là RETEST, link baseline và report cập nhật, các chuyển trạng thái và case bị chặn/chưa hoàn tất. Nếu retest bị chặn trước khi xác định được inventory, báo rõ chưa có case nào được xác minh lại.

## Tình huống minh họa để đối chiếu workflow

Các tình huống dưới đây là ví dụ giả định, không phải kết quả đã kiểm tra app.

- Case source `TC-003` từng FAIL: đọc lại đúng nhánh gây lỗi sau fix và đủ bằng chứng đạt → status lần này PASS, ghi chuyển FAIL → PASS và bằng chứng mới.
- `TC-004` từng PASS, không bị fix ảnh hưởng → vẫn thực hiện lại toàn bộ tiêu chí baseline; chỉ ghi PASS lần này khi có bằng chứng mới đạt expected.
- `TC-005` từng FAIL, lần này không đọc được file cấu hình cần đối chiếu do thiếu quyền truy cập → BLOCKED; ghi điều kiện đọc lại và giữ finding mở. Nếu đọc đủ source và xác định cấu hình bắt buộc vẫn không được triển khai thì FAIL.
- `TC-006` từng PASS nhưng dùng code chung bị fix tác động → kiểm tra lại theo baseline như các case source khác; nếu thấy sai thì ghi PASS → FAIL và finding mới, không sinh testcase mới.
- `TC-007` là case runtime từng FAIL → dẫn FAIL cũ ở lịch sử ngoài phạm vi, không đưa vào inventory source, tạo case thay thế hoặc đóng finding. Nhu cầu đánh giá source mới được ghi ở việc cần tiếp tục cho đợt TEST riêng.
- `TC-008` từng NOT_APPLICABLE → xác minh lại điều kiện áp dụng trên source hiện tại. Nếu tính năng đã được bật, thực hiện case với ID/expected baseline và ghi kết quả mới.
- Baseline có 10 case source, gồm 6 PASS, 2 FAIL, 1 BLOCKED và 1 NOT_APPLICABLE → cả 10 case đều thuộc phạm vi retest. Nếu blocker vẫn còn, ghi 1 BLOCKED cùng kết quả lần này của 9 case còn lại; không loại case, không thêm case và không báo đã hoàn tất toàn bộ.
- Retest lần hai dùng report retest lần một làm baseline → giữ nguyên ID, status gần nhất và lịch sử cả ba mốc TEST → RETEST 1 → RETEST 2; không tạo lại danh sách từ checklist.
