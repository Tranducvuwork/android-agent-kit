# Attribution

`android-agent-kit` gộp skill từ bốn nguồn. Bảng dưới ghi rõ skill nào từ repo nào, lấy ở commit nào, và
giấy phép của từng nguồn tại thời điểm lấy (**2026-11-10**).

## Tình trạng giấy phép

| Nguồn | Giấy phép | Phát hành lại công khai |
|---|---|---|
| [`LammaAndroid/qa_dev_test`](https://github.com/LammaAndroid/qa_dev_test) | không có file LICENSE — repo của chủ dự án | theo quyết định của chủ repo |
| [`huuphuoc1396/android-claude-skills`](https://github.com/huuphuoc1396/android-claude-skills) | **không có LICENSE** | ⚠️ cần xin phép tác giả |
| [`aihip/android-claude-code-skills`](https://github.com/aihip/android-claude-code-skills) | **không có LICENSE** (README ghi MIT) | ⚠️ cần xin phép tác giả |
| [`oh-ashen-one/android-agent-skills`](https://github.com/oh-ashen-one/android-agent-skills) | MIT | ✅ được, giữ nguyên bản quyền |

**Không có LICENSE nghĩa là tác giả bảo lưu mọi quyền.** Clone về xem và dùng nội bộ thì không sao, nhưng
đẩy một repo công khai chứa nội dung đó là phát hành lại. Trước khi public repo này, làm một trong các việc:

1. Mở issue hoặc nhắn hỏi tác giả `huuphuoc1396` và `aihip` xin phép, rồi ghi lại câu trả lời vào đây.
2. Hoặc để repo **private**, và thay phần vendor bằng script tự clone từ upstream lúc cài.
3. Hoặc bỏ hẳn hai nhóm skill đó khỏi `skills/` và chỉ giữ phần MIT + phần của chính bạn.

README của `aihip` ghi "License: MIT" nhưng repo không có file LICENSE — một dòng trong README không thay
được văn bản giấy phép, nên vẫn xếp vào nhóm cần hỏi.

---

## Nguồn theo từng skill

### `LammaAndroid/qa_dev_test` — commit `cb8a59114b20030876dfa4239aa698732cae193c`

Lấy từ file `qa_dev_test-main.zip` do chủ dự án cung cấp.

- `skills/android-app-policy-test/`
- `skills/android-automation-testing-setup/`
- `docs/dev-checklist.md`, `docs/testing-setup/`
- `scripts/prepare-skill.py`, `tests/`

Thay đổi tại chỗ: thêm khối `policy.allow_implicit_invocation: false` vào
`skills/android-automation-testing-setup/agents/openai.yaml` (bản gốc thiếu khối này, trong khi skill
anh em `android-app-policy-test` có).

### `huuphuoc1396/android-claude-skills` — commit `4ae1368596a1e8294857fd1f5163bd320a546cf7`

- `skills/scout/`
- `skills/rulebook/`
- `skills/spark/`
- `skills/mold/`
- `skills/slice/`
- `skills/blueprint/`
- `skills/forge/`
- `skills/foundry/`

Giữ nguyên, không sửa. Tên skill giữ như bản gốc để các tham chiếu chéo giữa chúng không gãy.

### `aihip/android-claude-code-skills` — commit `16a4a472c3e171ec03ec117c8d711d4bd4ea8d75`

- `skills/android-project-analyzer/`
- `skills/android-change-review/`
- `skills/android-translation-sync/`
- `skills/apk-analyzer/`
- `skills/figma-to-android/`

Giữ nguyên, không sửa. Ý tưởng xuất rule đa agent (`gemini-rules/`, `cursor-rules/`, `.toml` slash command)
lấy cảm hứng từ repo này, nhưng `scripts/install-skills.py` là code viết mới.

### `oh-ashen-one/android-agent-skills` — commit `84e2d167a2eb620552048b20501e114951a4ca28` — MIT

- `skills/adb-android-agent-control/`
- `skills/selector-first-ui-automation/`

Giữ nguyên, không sửa. Không lấy `autonomous-posting-verification-gates` (ngoài phạm vi).

```
MIT License

Copyright (c) 2026 oh-ashen-one

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Viết mới trong repo này

Không lấy từ nguồn nào, không ràng buộc giấy phép bên ngoài:

- `skills/android-screen-capture/` — SKILL.md, `scripts/capture-screen.sh`,
  `scripts/dump-to-outline.py`, `assets/templates/screens-template.md`, `agents/openai.yaml`
- `skills/android-feature-flow/` — SKILL.md, `agents/openai.yaml`
- `scripts/install-skills.py` — cài đa agent
- `scripts/validate-skills.py` — kiểm tra package skill
- `README.md`, `AGENTS.md`, `ATTRIBUTION.md`, `.github/workflows/validate-skills.yml`

## Cách cập nhật từ upstream

Các repo nguồn vẫn phát triển tiếp. Để lấy bản mới:

```bash
git clone --depth 1 https://github.com/<owner>/<repo>.git /tmp/upstream
diff -ru skills/<skill> /tmp/upstream/<path-to-skill>
```

Xem diff rồi mới merge, đừng ghi đè — và cập nhật commit hash trong file này sau khi merge.
