# Bộ khung VIPER cho dự án cá nhân

Đây là **template dùng lại**, chưa phải ứng dụng. Chưa chốt tên sản phẩm, chủ dự án hoặc stack.

## Tạo dự án mới

Chạy từ thư mục template:

```bash
python3 scripts/bootstrap.py my-personal-app \
  --target /Volumes/Hasty/my-personal-app \
  --name "Dự án cá nhân" \
  --authority "Tên bạn <email@example.com>"
```

Thay tên và thông tin chủ dự án bằng thông tin thật. Có thể bỏ `--authority` rồi điền sau.
Script từ chối ghi đè thư mục đã tồn tại, tạo Git riêng và thử tạo commit đầu; không tạo remote hoặc push.
Dùng `--dry-run` để xem trước. Giữ nguyên template này để tạo những dự án tiếp theo.

## Bắt đầu phát triển

Mở thư mục dự án vừa tạo trong công cụ làm việc của bạn.

- Codex: yêu cầu đọc `AGENTS.md`, `STATE.md` và dùng `$viper-validate` để bắt đầu pha V.
- Claude Code: đọc `CLAUDE.md`, chạy `/viper-validate`.
- Có tài liệu sản phẩm: đặt vào `intake/` theo `intake/README.md`.
- Chỉ có ý tưởng: bắt đầu đường phỏng vấn; pha V sẽ chốt nhu cầu, persona, phạm vi, stack và prototype.

Ở bản mới, `python3 scripts/gate.py V` báo chưa đạt là đúng vì tài liệu còn trống.
Các lệnh `make dev/check/test/migrate/deploy/doctor` là hợp đồng chưa có phần thân; hiện thực ở pha I.

## Thành phần giữ lại

VIPER V → I → P → E → R, tài liệu context, intake, skill stack, vai dùng thử, guard,
bootstrap và bộ tự kiểm. Hỗ trợ cả dự án một app và hệ thống nhiều target theo intake.
Không có code thuê xe, dữ liệu người dùng, cấu hình hạ tầng RentarViper hay lịch sử Git cũ.

## Kiểm tra template

```bash
python3 scripts/selftest.py
python3 scripts/gen_codex.py --check
```

Sửa hướng dẫn trong `CLAUDE.md` hoặc `.claude/` rồi chạy `python3 scripts/gen_codex.py`.
`AGENTS.md` và `.agents/skills/` là bản sinh, không sửa trực tiếp.

## Giới hạn tích hợp

Các thiết lập hook/MCP gốc thuộc Claude Code. Bản này bổ sung hướng dẫn và skill cho Codex,
chưa tự nối hook hoặc MCP cho Codex. Không coi việc có file cấu hình là bằng chứng guard đã chạy.
Bộ tự kiểm mặc định kiểm script/quy trình, không mở trình duyệt hoặc kiểm dogfood một sản phẩm thật.

## Nguồn

Trích 78 tệp từ commit `8ce907e7` của RentarViper: bản VIPER v1.9 ban đầu còn trống.
Bổ sung lớp Codex cục bộ và hướng dẫn này ngày 27/10/2026.
Các tuỳ biến nghiệp vụ, triển khai công ty và lịch sử các vòng sau không được mang sang.
