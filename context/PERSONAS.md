---
type: personas
tier: T0
status: DRAFT
last_reviewed: "{{DATE}}"
---

# PERSONAS — {{PROJECT_NAME}}

> **Ai dùng sản phẩm, và họ được cấp năng lực gì.** Điền ở pha V. Đây là nguồn sự thật cho
> phân quyền khi code (pha I), và là chân dung để 6 vai `viper-user-*` đóng khi dogfood —
> lăng kính hành vi (vội, phá, mới, khó tính…) là *cách dùng*, persona là *ai đang dùng*.
> Xoá hết dấu `_CHƯA ĐIỀN_` khi điền xong — `python3 scripts/gate.py V` bắt dấu này.

---

## 1. Persona

<!-- SỐ LƯỢNG khác nhau theo đường vào (VIPER.md §1.3):
     · Đường phỏng vấn — tối đa 2–3. Nhiều hơn là dấu hiệu scope quá lớn cho một tuần.
     · Đường intake   — bao nhiêu persona thì intake/PRD.md §2 định nghĩa bấy nhiêu; giữ
       nguyên mã P-… để truy vết ngược. Hệ thống lớn có nhiều vai là chuyện bình thường.

     Persona CHÍNH để đầu tiên. Ví dụ:

     ### Persona 1 — Chủ gara (role: owner) ← persona chính
     | Mục | Nội dung |
     |---|---|
     | Mã (intake) | P-OWNER |
     | Chân dung + bối cảnh | 35–50 tuổi, quản 3–10 thợ, đứng giữa xưởng vừa nghe điện thoại vừa thao tác, mỗi lần dưới 1 phút |
     | Thiết bị chính | Điện thoại (link chia sẻ qua Zalo) |
     | Mức thành thạo | Thấp — chỉ quen Zalo, không quen phần mềm quản lý |
     | Năng lực được cấp | Tạo/sửa/huỷ lịch hẹn của MỌI thợ trong gara mình; xem báo cáo tuần |
     | KHÔNG được làm | Thấy dữ liệu của gara khác |
     | Luồng chính | Nhận cuộc gọi → mở app → thấy khung giờ trống → chốt hẹn → xong |
     | Vào từ vòng | 1 |
-->

### Persona 1 — _CHƯA ĐIỀN_ (role: _CHƯA ĐIỀN_) ← persona chính

| Mục | Nội dung |
|---|---|
| Mã (intake) | — (đường phỏng vấn để `—`) |
| Chân dung + bối cảnh | _CHƯA ĐIỀN_ |
| Thiết bị chính | _CHƯA ĐIỀN_ (điện thoại / máy tính — vai `viper-user-mobile` ưu tiên thiết bị này) |
| Mức thành thạo | _CHƯA ĐIỀN_ |
| Năng lực được cấp | _CHƯA ĐIỀN_ (được làm gì trong sản phẩm) |
| KHÔNG được làm | _CHƯA ĐIỀN_ |
| Luồng chính | _CHƯA ĐIỀN_ (vai dogfood sẽ đi đúng luồng này) |
| Vào từ vòng | 1 |

<!-- Persona 2, 3… — copy đúng khung trên. Sản phẩm chỉ có một loại người dùng thì một
     persona là đủ, đừng bịa thêm cho có.
     "Vào từ vòng": persona chỉ xuất hiện ở vòng sau vẫn khai đủ ở đây (để ma trận §2
     đầy đủ ngay từ đầu), nhưng ghi rõ vòng nào mới cấp năng lực thật. -->

## 2. Ma trận vai × hành động

<!-- Đây là SPEC cho phân quyền — pha I code theo đây, không tự quyết rồi ghi DECISIONS.
     Mỗi ô ✗ là một ca kiểm bắt buộc: gọi thẳng URL/API phải bị chặn.
     `viper-user-breaker` (dogfood) và phép thử A↛B (/viper-polish nhóm 2) chạy đúng theo bảng này.
     Luôn có cột "chưa đăng nhập" — kể cả khi sản phẩm không có đăng nhập (khi đó ghi rõ
     "không có auth, mọi người thấy mọi thứ" ở dòng đầu và cân nhắc lại với Authority ở pha V).

     Ví dụ:
     | Hành động | owner | mechanic | chưa đăng nhập |
     |---|---|---|---|
     | Tạo / sửa / huỷ lịch hẹn | ✓ | ✗ | ✗ |
     | Xem lịch của thợ khác | ✓ | ✗ | ✗ |
     | Đánh dấu hoàn thành | ✓ | ✓ (của mình) | ✗ |
-->

| Hành động | _CHƯA ĐIỀN_ (role 1) | chưa đăng nhập |
|---|---|---|
| _CHƯA ĐIỀN_ | | |

## 3. Gán persona cho 6 vai dogfood

<!-- Mặc định mọi lăng kính đóng persona chính; đổi ở đây nếu muốn khác.
     Sản phẩm nhiều vai → chạy thêm lượt newbie cho từng persona còn lại nếu kịp.

     Cột "Đợt" là thứ /viper-dogfood đọc để chia lượt spawn. Sáu vai KHÔNG chạy cùng
     lúc: trình duyệt thì riêng (mcpServers inline + --isolated) nhưng server dev và DB
     dùng chung, nên vai ghi dữ liệu đè lên cảnh vai khác đang nhìn — và trạng thái rỗng
     chết ngay khi có bản ghi đầu tiên.
       Đợt 1 = cần DB SẠCH, đọc là chính.   Đợt 2 = cần DB CÓ DỮ LIỆU, ghi và phá.
     Giữa hai đợt: seed lại (deployment/local/). Tối đa 3 vai một đợt.
     Đổi cột này nếu sản phẩm có lý do riêng — ví dụ vai phá của bạn chỉ đọc, cho lên
     đợt 1 cũng được; nhưng đừng dồn quá 3 vai vào một đợt. -->

| Lăng kính | Persona đóng | Đợt |
|---|---|---|
| `viper-user-edge` | persona chính | 1 |
| `viper-user-newbie` | persona chính | 1 |
| `viper-user-picky` | persona chính, một experience + lát token của gói experience đó | 1 |
| `viper-user-rushed` | persona chính | 2 |
| `viper-user-breaker` | persona chính + đánh xuyên ranh giới vai theo ma trận §2 | 2 |
| `viper-user-mobile` | persona chính, viewport theo "Thiết bị chính" | 2 |

<!-- Đa target (đường intake): mỗi experience có persona riêng thì gán theo experience mà
     vòng này chạm tới, không dồn hết vào persona chính của cả hệ thống. -->
