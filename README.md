# Android Agent Kit

Bộ **19 agent skill** cho một project Android XML/Views, đi hết vòng đời một chức năng: chụp màn hình thật
trên máy → làm rõ yêu cầu → lên plan → implement → review diff → viết và chạy automation test → audit theo
dev checklist và Google Play policy.

Dùng chung cho **Claude Code**, **OpenAI Codex**, **Gemini CLI**, **Cursor** và **GitHub Copilot**: một bản
skill duy nhất trong `.agent-skills/`, mỗi agent có một cửa vào riêng trỏ về đó.

---

## Luồng chính

```
                  chạy một lần cho mỗi repo
scout → rulebook ───────────────────────────────────────────────────────────┐
                                                                            │
android-screen-capture → spark → [mold] → [slice] → blueprint → forge       │
      (chụp màn hình)    (cái gì) (thiết kế) (chia)   (plan)    (code)      │
                                                                            │
   → android-change-review → android-automation-testing-setup               │
          (review diff)              (test + evidence)                      │
   → android-app-policy-test ────────────────────────────────────────────────┘
          (audit checklist + Google Play)
```

`android-feature-flow` chạy toàn bộ sơ đồ trên trong một lần gọi. `foundry` chạy đoạn ngắn hơn
(spark → forge) khi chức năng không cần chụp màn hình, review hay test.

### Chụp màn hình → tài liệu → plan → code

Đây là mạch mà `android-screen-capture` mở ra:

1. Bạn mở màn hình cần làm trên máy thật (hoặc emulator) và báo "xong".
2. Agent chạy `capture-screen.sh`: lưu `<screen>.png`, view hierarchy `<screen>.uix` (uiautomator) và
   `<screen>.meta.json` (thiết bị, activity đang hiển thị, kích thước, density).
3. `dump-to-outline.py` đọc view hierarchy ra text: **copy nguyên văn**, `resource-id`, chỗ nào bấm được.
   Chữ và id lấy từ dump, không đoán từ ảnh; màu và khoảng cách đọc từ ảnh thì ghi rõ là `(estimated)`.
4. Agent viết `docs/features/<feature>/screens.md` — bảng màn hình, action, input, state, và map sang
   Activity/Fragment + layout trong source.
5. `spark` nhận `screens.md` làm đầu vào để chốt yêu cầu, `blueprint` ra plan, và plan **được review trước
   khi viết code** — review tại chỗ, hoặc đưa đường dẫn file plan cho Codex/Gemini review rồi mang kết quả
   về. Chỉ khi plan `Approved` thì `forge` mới chạy.

---

## Cài vào project Android

```bash
git clone https://github.com/<bạn>/android-agent-kit.git
cd android-agent-kit
python3 -I scripts/install-skills.py /đường/dẫn/tới/project-android
```

Mặc định cài **tất cả skill** cho **tất cả agent** bằng symlink. Các tuỳ chọn:

```bash
# chỉ một vài skill
python3 -I scripts/install-skills.py ~/StudioProjects/MyApp \
    --skill android-screen-capture --skill blueprint --skill forge

# chỉ một vài agent
python3 -I scripts/install-skills.py ~/StudioProjects/MyApp --agent claude-code codex

# copy thay vì symlink (môi trường không hỗ trợ symlink)
python3 -I scripts/install-skills.py ~/StudioProjects/MyApp --copy

# xem trước, không ghi gì
python3 -I scripts/install-skills.py ~/StudioProjects/MyApp --dry-run
```

Script không ghi đè thứ đã có sẵn; thêm `--force` nếu muốn thay.

### Cái gì được tạo ra trong project

```
.agent-skills/<skill>/          bản gốc duy nhất (SKILL.md + references + scripts)
.claude/skills/<skill>          Claude Code      → symlink
.agents/skills/<skill>          OpenAI Codex     → symlink
.github/skills/<skill>          GitHub Copilot   → symlink
.cursor/rules/<skill>.mdc       Cursor           → file rule sinh ra
.gemini/rules/<skill>.md        Gemini CLI       → file rule sinh ra
.gemini/commands/<skill>.toml   Gemini CLI       → slash command /<skill>
GEMINI.md                       Gemini CLI       → khối @import, chạy lại không nhân đôi
```

Sửa skill ở một chỗ (`.agent-skills/`), bốn agent kia thấy ngay. Riêng `.cursor/rules/` và `.gemini/rules/`
là file sinh ra từ `SKILL.md` — sửa ở repo này rồi chạy lại installer, đừng sửa tay.

Cập nhật sau này: `git pull` trong repo kit là xong (symlink), hoặc chạy lại installer với `--force`
(chế độ `--copy`).

---

## Danh sách skill

### Onboard repo (chạy một lần)

| Skill | Làm gì |
|---|---|
| `scout` | Đọc codebase, viết/cập nhật `CLAUDE.md`: setup, lệnh build/test, module, kiến trúc, quy ước, component dùng lại được |
| `rulebook` | Sinh rule theo từng tầng kiến trúc vào `.claude/rules/` |
| `android-project-analyzer` | Báo cáo kiến trúc, dependency, chất lượng code của cả project |

### Chụp màn hình và chốt yêu cầu

| Skill | Làm gì |
|---|---|
| `android-screen-capture` | Chụp màn hình app đang chạy + view hierarchy + activity, viết `screens.md` |
| `spark` | Hỏi theo vòng để làm rõ ý tưởng → `docs/features/<feature>/task.md` |
| `mold` | Đọc design (Figma, ảnh, draw.io) **một lần** → `design.md` + một file mỗi màn hình |
| `figma-to-android` | Từ design Figma ra XML + Kotlin |

### Lên plan

| Skill | Làm gì |
|---|---|
| `slice` | Chia task lớn thành subtask dọc, có thứ tự, review được |
| `blueprint` | Viết plan các bước build được, map từng bước vào acceptance criteria |

### Implement

| Skill | Làm gì |
|---|---|
| `forge` | Chạy plan đã duyệt: production code + unit test, compile sau mỗi bước |
| `foundry` | Chạy liền mạch spark → mold → slice → blueprint → forge |
| `android-feature-flow` | Chạy **toàn bộ** vòng: capture → … → forge → review → test → policy audit |

### Review và kiểm thử

| Skill | Làm gì |
|---|---|
| `android-change-review` | Review diff Android: crash risk, lifecycle, threading, regression |
| `android-automation-testing-setup` | Khảo sát app, viết và chạy automation theo package/workflow, thu evidence, báo cáo TEST/RETEST + coverage v2 |
| `android-app-policy-test` | Audit source theo dev checklist (32 rule) và chính sách Google Play, có TEST và RETEST |
| `apk-analyzer` | Soi APK: permission, chữ ký, component |
| `android-translation-sync` | Đồng bộ đa ngôn ngữ vào `strings.xml` |

### Điều khiển thiết bị

| Skill | Làm gì |
|---|---|
| `adb-android-agent-control` | ADB wireless, pairing, rediscover cổng, screenshot vs UI dump, vòng decide-act-verify |
| `selector-first-ui-automation` | Nhắm element bằng selector thay vì toạ độ, xử lý popup, giữ selector sống qua các bản app |

---

## Nguyên tắc không thương lượng

Bộ này viết cho việc nghiệm thu, nên mấy điều sau đứng trên mọi chế độ tự động:

- **Test không chạy thì không phải PASS.** Đọc source hay thấy có test code chỉ cho ra `NOT_TESTED`,
  không bao giờ cho ra `PASS`. Bốn trạng thái `PASS` / `FAIL` / `BLOCKED` / `NOT_TESTED` cộng lại
  phải bằng inventory.
- **Không sửa production để test chạy được.** `android-automation-testing-setup` chỉ đụng test code và
  cấu hình test tối thiểu, có production guard so hash trước/sau. Cần sửa production thì case là `BLOCKED`.
- **Plan chưa duyệt là chưa duyệt.** `forge` không chạy trước khi plan `Approved`.
- **Đường dẫn báo cáo phải tồn tại.** Kiểm tra trước khi nói đã ghi file.
- **Ảnh chụp màn hình là dữ liệu thật.** Trước khi commit, soi ảnh và dump xem có token, tài khoản thật,
  thông tin cá nhân không. Màn hình có thông tin đăng nhập thì mô tả bằng chữ, không kèm ảnh.

---

## Yêu cầu môi trường

| Thứ | Vì sao |
|---|---|
| Python **3.9+** | installer, validator, coverage validator, production guard |
| `adb` (Android platform-tools) | `android-screen-capture`, `adb-android-agent-control`, instrumentation test |
| Git | cài và cập nhật kit |
| Node.js 22.20+ | chỉ khi dùng `npx skills@latest` để cài theo cách của repo gốc `qa_dev_test` |

`install-skills.py` tự tìm `adb` theo `PATH`, rồi `ANDROID_HOME`, `ANDROID_SDK_ROOT`,
`~/Library/Android/sdk/platform-tools` và `~/Android/Sdk/platform-tools`.

Serial của thiết bị nối không dây có dấu cách (`adb-XXXX-YYY (2)._adb-tls-connect._tcp`) — luôn để trong
nháy kép khi truyền vào `--serial`.

---

## Phát triển kit

```bash
# kiểm tra mọi skill: frontmatter, tên, link, descriptor Codex, cú pháp script
python3 -I scripts/validate-skills.py

# đồng bộ docs/ nguồn vào package skill (checklist, tài liệu testing-setup)
python3 -I scripts/prepare-skill.py
python3 -I scripts/prepare-skill.py --check   # CI: fail nếu lệch
```

`docs/dev-checklist.md` và `docs/testing-setup/` là **nguồn**; bản trong `skills/*/references/` do
`prepare-skill.py` sinh ra. Sửa ở `docs/`, đừng sửa bản đã đóng gói.

---

## Nguồn gốc và giấy phép

Kit này gộp từ bốn repo. Xem [ATTRIBUTION.md](ATTRIBUTION.md) để biết skill nào từ đâu, commit nào, và
tình trạng giấy phép từng nguồn.

> ⚠️ Hai trong bốn nguồn (`huuphuoc1396/android-claude-skills`, `aihip/android-claude-code-skills`)
> **không có file LICENSE**. Mặc định đó là "bảo lưu mọi quyền": bạn xem và dùng riêng được, nhưng phát
> hành lại công khai thì cần xin phép tác giả trước. Chi tiết trong ATTRIBUTION.md.
