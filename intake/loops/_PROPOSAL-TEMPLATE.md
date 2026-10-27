# Kế hoạch vòng — mẫu cho `intake/loops/l<N>/_PROPOSAL.md` (đường intake)

> **Đặc tả định dạng, không phải chỗ điền.** Bản thật nằm ở `l<N>/_PROPOSAL.md` của
> từng vòng, do meta soạn ở **vòng 1** khi lập kế hoạch chia vòng
> ([VIPER.md §1.4](../../VIPER.md), `/viper-validate` mục I5).
>
> Đường phỏng vấn KHÔNG dùng file này — ở đó mỗi vòng Authority thả tài liệu vòng
> ([`_TEMPLATE.md`](_TEMPLATE.md)), không có kế hoạch lập sẵn.

---

## Vì sao có file này

Đường intake nhận cả một **hệ thống đã phân tích kỹ**, không phải một MVP. Việc đầu
tiên của pha V vòng 1 là cắt hệ thống đó thành N vòng: vòng nào giao capability nào,
chạm target nào, và **chạy tới pha nào**. Cắt xong thì kế hoạch phải nằm trên đĩa —
`context/ROADMAP.md §1` là bảng tổng (bản sống, nguồn sự thật), mỗi `_PROPOSAL.md`
là chi tiết của một vòng.

Authority ký **một lần cho cả kế hoạch** ở vòng 1, nên từ vòng 2 không phải ký lại
từng vòng. Đổi lại, mở vòng nào thì meta phải **rà lại** kế hoạch vòng đó — đối chiếu
kết quả vòng trước, chỉnh nếu lệch — rồi ghi dòng `Rà lại vòng N`. `gate.py V` đòi
đúng dòng đó với ngày ≥ `Vòng mở`; không có nó thì kế hoạch lập từ vòng 1 sẽ làm gate
mọi vòng xanh sẵn, và cơ chế vòng mất hết tác dụng.

---

## Cấu trúc chuẩn

Bốn dòng đầu nằm **ngoài** mọi khối `<!-- -->` — gate đọc chúng bằng máy.

```markdown
NGUỒN: KẾ HOẠCH VÒNG — lập ở vòng 1 ngày {{ISO}}, từ intake/ROADMAP.md §2 + intake/PRD.md §3
Pha vòng này: V, I
Thời lượng dự kiến: {{ví dụ: 1 tuần — theo cadence của wave tương ứng}}
UI vòng này: {{có màn mới | không có màn mới}}
Rà lại vòng {{N}}: {{để trống tới khi mở vòng — meta ghi ngày ISO lúc đó}}
```

| Dòng | Luật |
|---|---|
| `Pha vòng này` | **Luôn có `V, I`** — hai pha này bắt buộc ở mọi vòng, gate tự thêm vào nếu khai thiếu. Thêm `P` (deploy) · `E` (đo) · `R` (quyết go/pivot/kill) ở vòng Authority chốt. Vòng không khai P thì `gate.py P1/P2` tự bỏ qua |
| `Thời lượng dự kiến` | Đường intake không bị ép "1 tuần mỗi vòng" — lấy nhịp từ wave cadence của `intake/ROADMAP.md` |
| `UI vòng này` | `không có màn mới` → gate V bỏ qua prototype cho vòng đó (bản đồ màn + design system vòng trước còn hiệu lực) |
| `Rà lại vòng N` | Ghi **khi mở vòng**, không ghi trước. Ngày phải ≥ `Vòng mở` trong `STATE.md` |

---

## Mục tiêu vòng

Một đoạn: vòng này xong thì sản phẩm làm được gì mà trước đó chưa làm được. Viết theo
góc nhìn người dùng, không phải theo góc nhìn module.

## Phạm vi — capability giao ở vòng này

Giữ nguyên mã `CAP-…` của intake để truy vết ngược. Cột "Target" trỏ thư mục code
(`srcroot/<nhóm>/<tên>/`) theo `context/ARCHITECTURE.md §1–§3`.

| Capability | Persona | Target | AC dự kiến |
|---|---|---|---|
| `{{CAP-XXX-01}}` — {{mô tả ngắn}} | `{{P-XXX}}` | `srcroot/boundaries/{{tên}}` | {{AC-1, AC-2}} |

> AC dự kiến ở đây là bản nháp; AC thật chốt trong `context/PRD.md §3` ở pha V của
> vòng đó, và phải truy được về đúng capability này qua `context/CAPABILITIES-MAP.md`
> (gate V đường intake kiểm điều đó thay cho trần 7 AC).

## Phụ thuộc vòng trước

Thứ vòng này cần mà vòng trước phải giao xong. Không có thì ghi `—`.

| Cần gì | Từ vòng | Hỏng thì sao |
|---|---|---|

## Legacy được phép phá

Mặc định vòng mới **không được phá** thứ người dùng đang xài
(`context/BACKWARD-COMPATIBILITY-CHECKLIST.md`). Đây là một trong ba nơi hợp lệ để
Authority cho phép phá — hai nơi kia là file `.md` Authority thả vào cùng thư mục, và
chốt qua chat ở pha V (meta ghi hộ vào thư mục này). Không ghi ở đâu cả thì meta phải
giữ tương thích, và `guard_ds`/`guard_bc` sẽ chặn đúng chỗ.

| Phá gì | Ai/dữ liệu đang dùng | Đường di trú |
|---|---|---|

## Điều chỉnh khi mở vòng

Kế hoạch lập ở vòng 1 gặp thực tế thì lệch — chỗ ghi lại là đây, không phải sửa lén
rồi im. Mỗi lần rà lại mà thấy phải đổi thì thêm một dòng.

| Ngày | Đổi gì | Vì sao |
|---|---|---|

---

## Ba luật của `_PROPOSAL.md`

1. **Meta soạn, Authority sửa.** File này do meta sinh ở vòng 1 từ tài liệu intake.
   Authority sửa thẳng vào đây, hoặc thả một `.md` thường vào cùng thư mục — meta đọc
   cả hai, và ghi chỗ lệch vào `## Điều chỉnh khi mở vòng`.
2. **Đổi kế hoạch thì đổi cả hai chỗ.** `context/ROADMAP.md §1` và `_PROPOSAL.md` phải
   khớp nhau — `gate.py V` vòng 1 đối chiếu số dòng kế hoạch với số `_PROPOSAL.md` có
   thật. Thêm vòng ngoài kế hoạch cũng đi đúng đường này.
3. **Đóng băng sau khoá scope của vòng đó.** Khoá scope vòng N xong thì `l<N>/` không
   sửa nữa; muốn đổi ý giữa vòng là ngoài scope → `context/ROADMAP.md` chờ vòng sau.
