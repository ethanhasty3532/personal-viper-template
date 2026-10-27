---
name: viper-dogfood
description: Tự dùng sản phẩm + spawn 6 subagent đóng persona dùng thử theo 6 góc nhìn, chạy HAI ĐỢT mỗi đợt tối đa 3 vai — bắt buộc trước khi báo xong
---

# $viper-dogfood — "You eat your own shit"

> **LUẬT #8.** Không báo xong khi chưa tự dùng. Bắt buộc cuối pha I (ở local) và cuối pha P (trên production).
> Không hỏi Authority trong suốt lệnh này — phát hiện thì xử hoặc ghi lại.

Đọc code rồi suy ra "chắc chạy được" không tính. Phải mở ra bấm.

## Bước 1 — Chuẩn bị

```bash
make dev        # đảm bảo đang chạy
```

Lấy URL đang chạy (mặc định `http://localhost:3000` hoặc `:8000`). Ở pha P thì dùng URL production.

Đọc:
- `context/PRD.md §3` (AC) và `context/ARCHITECTURE.md §7` (luồng lõi) — thứ phải đi hết
- `context/PERSONAS.md` — persona nào đóng vai nào (§3), năng lực từng vai (§2)
- `context/PROTOTYPE.md` — bản đồ màn hình Authority đã chốt (bỏ qua nếu có marker `KHÔNG CÓ UI`)
- `context/DESIGN-SYSTEM.md` — §2 bảng token · §4 trạng thái bắt buộc từng component · §5 khuôn rỗng/lỗi/đang tải (nếu có UI). Nhiều design system (§0) → xem cột `Design system` ở `ARCHITECTURE.md §2–§3` để biết experience nào mặc gói nào; `viper-user-picky` cần lát token đúng gói

Cần dữ liệu mẫu → tạo theo `PRD.md §7`. Không có dữ liệu thì không dùng thử được, mà cũng là một phát hiện: người dùng mới vào cũng gặp cảnh y hệt.

## Bước 2 — Meta tự tay dùng

**Đích thân, trước khi giao cho ai.** Mở trình duyệt bằng skill `viper-browse`, đóng vai **persona chính** (`PERSONAS.md §1`), đi hết luồng lõi như persona đó:

- Vào từ trang đầu, không nhảy thẳng vào URL trong
- Đi hết luồng ở `ARCHITECTURE.md §7` từ đầu đến cuối
- Kiểm từng AC trong `PRD.md §3` — làm được thật không, hay chỉ "về lý thuyết là được"
- Đối chiếu từng màn với `PROTOTYPE.md §1`: thông tin bắt buộc có đủ và đúng thứ tự ưu tiên không — **lệch bản Authority đã chốt là phát hiện**, không phải chuyện thẩm mỹ
- Soi hình thức theo `DESIGN-SYSTEM.md`: nút đang gửi có khoá lại không, lỗi có theo khuôn §5 không, có màu/kiểu lạc loài ngoài token không — token là thứ Authority đã chốt, lệch là phát hiện. Đây là lượt nhìn nhanh của meta; `viper-user-picky` ở đợt 1 mới là lượt **đo** bằng computed style

Ghi lại mọi thứ vướng, kể cả thứ nhỏ: chữ khó hiểu, nút không rõ bấm để làm gì, chờ mà không biết có đang chạy không, quay lại thì mất dữ liệu đang nhập.

## Bước 3 — Spawn 6 subagent, HAI ĐỢT, mỗi đợt tối đa 3 vai

> **Vì sao không thả cả 6 cùng lúc.** Trình duyệt thì đã riêng cho từng vai rồi
> (`mcpServers` inline + `--isolated` trong frontmatter). Nhưng **server dev và DB thì
> dùng chung**: `breaker` đổ dữ liệu bậy và `rushed` tạo bản ghi trùng ngay giữa lúc
> `newbie` đang nhìn màn, nên người này thấy cảnh của người kia. Nặng nhất là trạng
> thái rỗng — thứ `viper-user-edge` coi là quan trọng nhất — chết ngay khi bất kỳ vai
> nào tạo bản ghi đầu tiên. Chia đợt là để tách chỗ dùng chung đó, không phải để tách
> trình duyệt.

Phân vai và phân đợt theo `PERSONAS.md §3` (mặc định: persona chính). Mặc định là:

**Đợt 1 — DB SẠCH, đọc là chính.** Gửi cả 3 trong **một** lượt.

| Agent | Lăng kính (CÁCH dùng) | Đi tìm |
|---|---|---|
| `viper-user-edge` | Rỗng / mất mạng / API lỗi / nhiều dữ liệu | Trạng thái biên hiện gì — **rỗng phải đo TRƯỚC khi ai ghi gì** |
| `viper-user-newbie` | Lần đầu, không biết gì | Persona mới có tự hiểu phải làm gì không, trên đúng cảnh người mới thật gặp |
| `viper-user-picky` | Khó tính về **hình thức** | Màu/chữ/nhịp lệch token · tương phản · trạng thái component · khuôn rỗng §5 |

**Giữa hai đợt — seed lại.** Đợi đủ 3 vai đợt 1 trả kết quả, rồi đưa DB về mốc có dữ liệu: chạy seed ở `deployment/local/`. Chưa có bước seed thì tạo dữ liệu mẫu bằng tay theo `PRD.md §7` và ghi 1 dòng `DECISIONS.md` (thiếu seed là một phát hiện của chính lượt dogfood này).

**Đợt 2 — DB CÓ DỮ LIỆU, ghi và phá.** Gửi cả 3 trong **một** lượt.

| Agent | Lăng kính (CÁCH dùng) | Đi tìm |
|---|---|---|
| `viper-user-rushed` | Bấm nhanh, bỏ giữa chừng, quay lại | Dữ liệu có hỏng, có kẹt trạng thái không |
| `viper-user-breaker` | Nhập bậy, gửi hai lần, vượt quyền | Validate + **phân quyền theo ma trận `PERSONAS.md §2`** — mỗi ô ✗ là một ca phải thử |
| `viper-user-mobile` | Màn hình nhỏ, theo thiết bị chính của persona | Vỡ giao diện, không bấm được — **bảng dài mới tràn, danh sách dài mới vỡ** |

**Ba ràng buộc cứng**: tối đa **3 vai một đợt** · **không mở đợt 2 khi đợt 1 chưa xong** · **giữa hai đợt phải seed lại**. Muốn đổi vai nào vào đợt nào thì sửa cột `Đợt` ở `PERSONAS.md §3`, đừng sửa trong đầu.

Mỗi agent nhận trong prompt:
1. URL + tóm tắt sản phẩm làm gì
2. **Persona được giao**: chân dung + bối cảnh + năng lực được cấp + luồng chính (chép từ `PERSONAS.md §1` — persona là *bạn là ai*, lăng kính là *cách bạn dùng*)
3. Luồng lõi từ `ARCHITECTURE.md §7` + AC liên quan
4. Các màn hình liên quan từ `PROTOTYPE.md §1` để đối chiếu (nếu có UI)
5. Riêng `breaker`: ma trận vai × hành động `PERSONAS.md §2` + tài khoản thử cho từng vai
6. Riêng `picky`: **đúng một experience** + **lát token của gói mà experience đó mặc** (`DESIGN-SYSTEM.md §2`, lọc theo cột `Design system` ở `ARCHITECTURE.md §2–§3`) + trạng thái bắt buộc §4 + ba khuôn §5. Sản phẩm một design system → cả bảng token. Nhiều design system → **một experience một lượt**, trộn hai bảng vào một lượt là mất sạch ý nghĩa của chữ "màu lạ"

Sản phẩm nhiều vai → chạy thêm lượt `newbie` cho từng persona còn lại nếu kịp; tối thiểu `breaker` phải thử đủ mọi ranh giới vai trong ma trận.

**Vòng ≥ 2 — lượt regression bắt buộc**: legacy là hợp đồng (`$viper-repeat`). Meta (Bước 2) và `viper-user-rushed` (đợt 2) đi lại **luồng lõi các vòng trước** (AC trong `archive/vong-*/PRD.md`), không chỉ luồng mới — tính năng cũ gãy vì code mới là phát hiện nặng ngang gãy luồng lõi, xử ở Bước 4 dòng đầu tiên.

**Chế độ intake, đa target**: đi hết luồng lõi trên **từng experience có UI thuộc phạm vi vòng này** (`intake/loops/l<N>/_PROPOSAL.md` cột Target, đối chiếu `ARCHITECTURE.md §2–§3`) — mỗi experience một URL local riêng, đừng chỉ thử cái dễ mở nhất. **Lặp cặp đợt cho từng experience**: số lượt = số experience có UI trong phạm vi vòng, không nhồi 6 vai × N target vào một lượt. Luồng đi **xuyên nhiều target** (một hành động ở experience A phải hiện ra ở experience B) là chỗ dễ gãy nhất và bắt buộc phải thử thật, không suy ra từ code.

## Bước 4 — Xử phát hiện

Gộp phát hiện của mình + 6 agent (cả hai đợt), phân loại:

| Loại | Xử |
|---|---|
| Hỏng luồng lõi, mất dữ liệu, lỗ hổng phân quyền | **Sửa ngay**, không hoãn |
| **Trộn design system** — experience dùng token của gói khác | **Sửa ngay**, ngang lỗ phân quyền: mỗi gói là một hợp đồng hình thức riêng, mượn token gói khác là phá cả hai |
| Lệch `DESIGN-SYSTEM.md`: màu/chữ/nhịp ngoài lát token · thiếu trạng thái bắt buộc §4 · sai khuôn §5 | Sửa về token đã chốt; cố ý giữ khác → 1 dòng `DECISIONS.md`; đổi chính token → 1 dòng `DESIGN-SYSTEM.md §7` |
| Lệch `PROTOTYPE.md` đã chốt | Sửa theo prototype; cố tình giữ khác → 1 dòng `DECISIONS.md` |
| Nhỏ, sửa dưới 15 phút | Sửa ngay |
| Cần nhiều thời gian nhưng trong scope | `STATE.md §Phát hiện từ dogfood chưa xử` |
| Ngoài scope đã khoá | `ROADMAP.md` backlog |

Sửa xong chạy lại `make check`, và **dùng lại** phần vừa sửa.

## Bước 5 — Kết luận

Báo cho Authority theo dạng này:

```
Đã dùng thử ở <local|production>, đóng vai <persona>, 2 đợt × 3 vai

Luồng lõi:     đi hết được / gãy ở bước <n>
AC:            <x>/<y> làm được thật
Phân quyền:    <x>/<y> ô ✗ trong ma trận đã thử, chặn đúng hết / thủng ở <đâu>
Prototype:     khớp bản đã chốt / lệch ở <màn nào> (n/a nếu không có UI)
Design system: <x> màu lạ · <y>/<z> cặp tương phản đạt · <a>/<b> component đủ trạng thái
               trộn DS: không / <experience> dùng token của gói <ds>

Đã sửa ngay:      <danh sách>
Ghi lại chưa xử:  <danh sách + ở đâu>
Đẩy sang Phase 2: <danh sách>
```

## Dấu hiệu dogfood giả

Nếu cả 6 agent đều báo "không thấy vấn đề gì" ngay lần đầu — **gần như chắc chắn chúng không thực sự dùng**. Sản phẩm mới dựng trong một ngày luôn có chỗ vướng. Gặp trường hợp này: kiểm lại xem agent có mở trình duyệt thật không, có bấm thật không, hay chỉ đọc code rồi suy ra. Rồi cho chạy lại với yêu cầu nêu **thao tác cụ thể đã làm** và **thứ nhìn thấy trên màn hình**.

Riêng `viper-user-picky`: báo "khớp hết" mà **không nêu được một giá trị computed style nào** thì nó đã đọc `DESIGN-SYSTEM.md` rồi suy ra chứ chưa mở trình duyệt. Vai này phải trả về số đo thật (`rgb(37, 99, 235)`, `13px`) kèm selector — không có số đo thì không tính là đã soi.

Một dấu hiệu giả nữa: báo cáo không nêu được mình đóng persona nào, hoặc đi một luồng chẳng liên quan gì đến luồng chính của persona — tức là đã thử như "người dùng nói chung", đúng thứ `PERSONAS.md` sinh ra để tránh.

Điều này áp cho cả chính mình ở bước 2.
