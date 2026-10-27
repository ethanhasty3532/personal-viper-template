---
type: viper-policy
version: 1.8
tier: T0
owner: Authority (solo)
last_reviewed: "{{DATE}}"
---

# VIPER v1.9 — quy trình solo, hai đường vào

> **Đây là tài liệu T0.** Mọi tài liệu khác trong repo phải nhất quán với file này. Conflict → file này thắng.

---

## 0. VIPER dùng cho việc gì

VIPER có **hai đường vào**, cho hai bối cảnh khác nhau. Chúng dùng chung 5 pha, 8 luật, hợp đồng lệnh và cơ chế gate — nhưng **ràng buộc về cỡ sản phẩm và nhịp thì khác nhau**. Áp luật của đường này sang đường kia là lỗi thiết kế, không phải sự nghiêm khắc.

| | **Đường phỏng vấn** (mặc định) | **Đường intake** (§1.3) |
|---|---|---|
| Xuất phát từ | Founder/PO có một ý tưởng trong đầu | Bộ tài liệu MESH-render đã phân tích kỹ, thả vào `intake/` |
| Để làm gì | Test thị trường / test quan điểm / test phản ứng trên một pain point | Giao một **hệ thống đã được thiết kế**, chia thành nhiều vòng chạy dần |
| Cỡ sản phẩm | 1 app, 1 database, 1 nơi deploy | **Nhiều boundary + nhiều experience** theo intake ARCHITECTURE, code ở `srcroot/<nhóm>/<tên>/` |
| Nhịp | Một tuần, khoá scope trong 2 tiếng | Mỗi vòng tự khai thời lượng theo wave cadence của intake |
| Số vòng | Không lập trước — vòng sau mở khi pha R quyết GO/PIVOT | **Lập ở vòng 1** (§1.4): N vòng, mỗi vòng một `_PROPOSAL.md` |
| Pha mỗi vòng | Trọn V-I-P-E-R trong tuần | **V + I bắt buộc**; P/E/R chỉ ở vòng Authority chốt |

**Chung cho cả hai:**

| Hợp | Không hợp |
|---|---|
| Một người quyết tất (solo Authority) | Nhiều Authority phải sign-off chéo |
| Rủi ro sai thì làm lại rẻ | Sai là mất tiền/mất dữ liệu người dùng ở quy mô lớn |
| Sản phẩm production-ready thật, không phải bản demo | Cần contract signing + wave orchestration nhiều đội |

Đường phỏng vấn thêm hai ràng buộc riêng: phạm vi khoá được trong 2 tiếng, và không micro-service. Vượt ngưỡng đó mà **chưa** có tài liệu phân tích → dùng MESH (§7 Đường nâng cấp). Vượt ngưỡng đó mà **đã** có tài liệu MESH-render → đi đường intake, đó chính là chỗ nó sinh ra để giải quyết.

VIPER là bản chắt lọc của MESH v4.6: giữ **context là nguồn sự thật · quyết định phải có vết · gate trước khi đi tiếp**; bỏ đa Authority, contract signing giữa các đội, wave orchestration nhiều repo. Hook chặn giữ đúng **ba** cái: `AskUserQuestion` ngoài pha V, deploy khi vòng ≥2 còn nợ tương thích ngược, và ghi prototype/design system lệch bản đã chốt (§3c).

---

## 1. Năm pha

```
V ──► I ──► P ──► E ──► R
Validate  Implement  Polish&Publish  Evaluate  Repeat

phỏng vấn:  D1 sáng   D1 còn lại   D2           D2–D5      cuối tuần
            (2–3h)    (bắt buộc)   (khuyến nghị)(tuỳ chọn)

intake:     mọi vòng  mọi vòng     ── chỉ ở vòng khai trong _PROPOSAL.md ──
            (bắt buộc)(bắt buộc)
```

| Pha | Việc |
|---|---|
| **V — Validate** | Hiểu sản phẩm cho đủ sâu (phỏng vấn gộp, hoặc dịch tài liệu intake) → chốt vấn đề, persona + năng lực được cấp, phạm vi, tiêu chí thành công, stack; có UI → chốt **design system** (token · tương phản · kho component) rồi dựng **prototype tương tác** từ đó cho Authority bấm thử và **chốt** trước khi khoá scope |
| **I — Implement** | Meta challenge builder → scaffold từ stack skill → walking skeleton → luồng lõi → tự dùng thử |
| **P — Polish & Publish** | Prod-ready checklist 4 nhóm → deploy PaaS |
| **E — Evaluate** | Đo phản ứng, fix bug, tối ưu, thử nghiệm |
| **R — Repeat** | Quyết định go / pivot / kill. Đóng vòng, **mở vòng mới** (§1.2): vòng sau là một lượt V→I→(P)→(E)→(R) nữa trên cùng repo, không phải "code tiếp" |

**Pha nào bắt buộc — khác nhau theo đường vào:**

- **Đường phỏng vấn**: V và I bắt buộc trong ngày 1; từ P trở đi tuỳ tình hình, nhưng release phải rơi vào trong tuần. Một vòng = trọn V-I-P-E-R.
- **Đường intake**: **V và I bắt buộc ở MỌI vòng**; P, E, R chỉ chạy ở vòng nào Authority chốt — khai trong `intake/loops/l<N>/_PROPOSAL.md` dòng `Pha vòng này` (§1.4). Hệ thống lớn thì phần lớn vòng giữa chỉ V+I: chưa đủ thứ đáng deploy thì deploy chỉ là nghi thức, và chưa deploy thì không có gì để đo. `gate.py P1/P2/E` tự bỏ qua ở vòng không khai pha đó.

Không có stage machine. Gate chỉ báo, không chặn: `python3 scripts/gate.py <pha>`. Có đúng **ba** hook chặn — `AskUserQuestion` ngoài pha V (`scripts/guard_ask.py`), lệnh deploy khi vòng ≥2 còn mục tương thích ngược chưa rà (`scripts/guard_bc.py`), và ghi prototype/`DESIGN-SYSTEM.md` lệch design system đã chốt (`scripts/guard_ds.py`): thực chiến cho thấy cấm bằng văn xuôi không giữ được luật, nhất là sau compact.

### 1.1 Gate rời pha — bản chuẩn

> **Đây là định nghĩa gate DUY NHẤT.** `CLAUDE.md §2`, `STATE.md §Gate` và `scripts/gate.py` đều là bản sao thao tác của bảng này. Lệch nhau → bảng này thắng, sửa ba chỗ kia cho khớp (luật #4).
>
> Chỗ nào ghi *(phỏng vấn)* / *(intake)* là chỗ hai đường khác nhau; `gate.py` nhận diện chế độ qua marker `NGUỒN: INTAKE` trong `INTERVIEW.md` — một cơ chế duy nhất, dùng cho mọi rẽ nhánh.

| Gate | Điều kiện | Máy kiểm được? |
|---|---|---|
| **V** | `PRD.md` đủ mục (pain point · đối tượng · AC · out-of-scope · 1 success metric có số) | ✓ |
| | Số AC: *(phỏng vấn)* 3–7, quá 7 là scope quá lớn cho một tuần · *(intake)* ≥3, **không trần** — đổi lại mọi `AC-n` phải có mặt ở `CAPABILITIES-MAP.md` cột "AC vòng này" | ✓ |
| | *(vòng 1 — phỏng vấn)* `INTERVIEW.md`: 14 mục, mỗi mục có dòng `Bằng chứng:` không rỗng (câu chuyện thật / con số / hiện vật) | ✓ |
| | *(vòng 1 — intake, §1.3 — thay cho dòng trên)* `intake/PRD.md` là render thật (không rỗng, hết `{{…}}`, có dòng `CAP-`) · `INTERVIEW.md` mang marker `NGUỒN: INTAKE` + bảng `## Truy vết intake → context` · `CAPABILITIES-MAP.md` đã tách từ intake PRD §3 · **kế hoạch vòng** (§1.4): `ROADMAP.md §1` có ≥1 dòng và mỗi dòng có `intake/loops/l<N>/_PROPOSAL.md` tương ứng | ✓ |
| | *(vòng ≥2 — phỏng vấn; thay cả hai dòng trên, `INTERVIEW.md` đóng băng)* `intake/loops/l<N>/` có ≥1 file `.md` thật từ Authority (không rỗng, hết `{{…}}`, không tính `_*.md`) — tài liệu này đồng thời là **chữ ký chốt** của Authority | ✓ |
| | *(vòng ≥2 — intake; thay dòng trên)* `l<N>/_PROPOSAL.md` là kế hoạch thật (hết `{{…}}`, có dòng `Pha vòng này`) + dòng `Rà lại vòng N: <ISO>` ngày ≥ `Vòng mở`. Authority đã ký một lần cho cả kế hoạch ở vòng 1; dòng rà lại là dấu vết meta thật sự đọc lại khi mở vòng | ✓ |
| | ≥2 quyết định `DECISIONS.md` của vòng này — **mọi vòng, kể cả vòng 1** (tối thiểu: lý do chọn stack + một quyết định lớn khác). *(vòng ≥2)* chỉ đếm dưới mốc `(vòng N)` đúng số vòng, ngày ≥ `Vòng mở`; challenge V cũng tính riêng của vòng (ngày ≥ `Vòng mở`). Thiếu mốc/`Vòng mở` (không mở vòng bằng `repeat.py`) → fail-closed | ✓ |
| | `PERSONAS.md`: ≥1 persona + năng lực được cấp + ma trận vai × hành động. Số persona: *(phỏng vấn)* tối đa 3 (thường 2–3; một loại người dùng thì 1 là đủ) · *(intake)* theo intake PRD, giữ mã `P-…` | ✓ |
| | `TECHSTACK.md` chốt stack + 1 dòng lý do trong `DECISIONS.md`. *(intake)* per-target, **intake thắng default của stack skill** | ✓ |
| | `ARCHITECTURE.md`: sơ đồ · mô hình dữ liệu · ca biên · luồng lõi. *(intake)* thêm danh sách boundary/experience + contract giữa target | ✓ |
| | Có UI: `DESIGN-SYSTEM.md` đủ mục **trước khi dựng prototype** — token được prototype dùng thật · prototype không dùng token ngoài bảng · tương phản đạt WCAG AA (gate tự tính từ mã hex) · component nào cũng có màn hình dùng. Có gói `intake/design-systems/<ds>/tokens.json` → token phải khớp gói (không bịa · không bỏ rơi · không lệch giá trị), **đối chiếu riêng từng gói**. Nhiều gói → §2 phải có cột `DS` và mọi experience ở `ARCHITECTURE §2–§3` phải khai `Design system`; `prototype/<exp>/` chỉ được dùng lát token của gói mình. Backend-only: bỏ qua theo marker | ✓ |
| | Có UI: `PROTOTYPE.md` đủ mục + prototype tương tác + **Authority đã chốt** + mọi AC map vào màn hình + **mọi màn khai ở §1 đều đã dựng**. File: *(phỏng vấn)* `prototype/index.html` · *(intake)* `prototype/<experience>/index.html`, gate glob `prototype/**/*.html`. Backend-only: marker `KHÔNG CÓ UI`. *(intake, vòng ≥2)* `_PROPOSAL.md` khai `UI vòng này: không có màn mới` → bỏ qua cả cụm | ✓ |
| | Challenge pha V **PASS** ở `STATE.md §Challenge log` — 3–5 câu khó nhất, trả lời được chỉ từ tài liệu | ✓ |
| | **Scope khoá** — từ đây không hỏi Authority nữa | người |
| **I** | Challenge **PASS** ghi ở `STATE.md §Challenge log` (§3b) | ✓ |
| | `make dev` · `make check` · `make migrate` đã hiện thực | ✓ |
| | Đã có commit code ngoài commit khởi tạo | ✓ |
| | Luồng lõi end-to-end bấm được ở **local** · `make check` xanh | người |
| | **Đã chạy `/viper-dogfood`**, phát hiện đã xử hoặc đã ghi | người |
| **P1**<br>*(vào publish)* | *(intake)* Vòng không khai `P` trong `_PROPOSAL.md` → **bỏ qua toàn bộ gate P**, đi thẳng `/viper-repeat` (§1.4) | ✓ |
| | 4 nhóm `PRODUCTION-READY.md` xanh — **trừ** mục gắn `(sau deploy)` | ✓ |
| | Vòng ≥2: `BACKWARD-COMPATIBILITY-CHECKLIST.md §3` xanh — legacy được giữ (hook `guard_bc` chặn deploy theo đúng phép đếm này) | ✓ |
| | `make test` · `make deploy` · `make doctor` đã hiện thực | ✓ |
| | `make check && make test` xanh · phép thử phân quyền A↛B đã chạy ở local | người |
| **P2**<br>*(rời pha P)* | 4 nhóm xanh **toàn bộ**, kể cả mục `(sau deploy)` | ✓ |
| | `DEPLOY.md` đủ §1–§5, **có rollback** — điền TRƯỚC lần deploy đầu | ✓ |
| | Production sống, health check 200 · smoke test trên production pass | người |
| | **Đã THỬ rollback một lần** | người |
| | **Đã chạy `/viper-dogfood` lần 2 trên production** | người |
| **E** | *(intake)* Vòng không khai `E` → **bỏ qua gate E** (chưa deploy thì không có gì để đo) | ✓ |
| | Tracking đang đếm thật · ngưỡng go/pivot/kill ghi TRƯỚC khi nhìn số | người |
| | Sổ EXPERIMENTS **của vòng này** có dòng số liệu thật (vòng 1: `EXPERIMENTS.md`; vòng N ≥2: `EXPERIMENTS-v<N>.md`) | ✓ |
| **R** | Quyết định go / pivot / kill ghi ở `DECISIONS.md` + sổ EXPERIMENTS của vòng. *(intake)* Vòng không chạy `E` → không có số liệu, R rút về sổ sách: đóng vòng, mở vòng kế theo kế hoạch | người |
| | `ROADMAP.md` cập nhật — backlog §3, và *(intake)* trạng thái vòng ở §1 | người |
| | Vòng mới mở bằng `scripts/repeat.py --go` — archive snapshot, sổ sách theo vòng, **không reset gì** (§1.2) | ✓ script |

**Vì sao pha P có hai gate.** Bốn mục production-ready không thể làm khi chưa có production: backup đã thử khôi phục · HTTPS · push-là-deploy · analytics đang đếm. Bắt đủ cả 4 nhóm rồi mới cho deploy thì không bao giờ deploy được. Chúng gắn nhãn `(sau deploy)` trong `PRODUCTION-READY.md`; `P1` bỏ qua, `P2` đòi đủ.

**Gate bỏ qua ≠ gate lỏng.** Vòng khai `V, I` thì `gate.py P1/P2/E` in ✓ kèm lý do và không đếm mục nào — nhưng gate V và I của vòng đó vẫn đầy đủ, và `repeat.py` cảnh báo nếu vòng khai `P`/`E` mà thực tế chưa deploy / chưa có số liệu. Cắt pha là quyết định của kế hoạch, không phải cửa để bỏ dở.

### 1.2 Vòng — Phase 2 trở đi

Một **vòng** = một lượt V→I→(P)→(E)→(R). Vòng hiện tại ghi ở `STATE.md` (`Vòng: N`). Vòng mới mở bằng `scripts/repeat.py --go` (lệnh `/viper-repeat`), không code tiếp trên vết vòng cũ nhưng cũng **không xoá vết đó đi**.

Vòng sau **mở vì lý do khác nhau theo đường vào**:

- **Đường phỏng vấn** — mở khi pha R quyết GO/PIVOT từ số liệu. Không biết trước có vòng 2 hay không; đó là toàn bộ ý nghĩa của việc test thị trường.
- **Đường intake** — mở theo **kế hoạch đã lập ở vòng 1** (§1.4). Biết trước có bao nhiêu vòng và mỗi vòng làm gì, vì tài liệu intake đã phân tích xong; pha R của vòng có chạy E vẫn quyết go/pivot/kill như thường, và quyết định đó có thể sửa kế hoạch.

**KHÔNG có cơ chế reset.** Tài liệu sống tiến hoá liên tục qua các vòng: `INTERVIEW.md` đóng băng làm hiện vật vòng 1 (phỏng vấn là công cụ mở rộng tư duy lúc khởi đầu — từ vòng 2 dự án đã hình thành, insight nằm ở số liệu), các sổ EXPERIMENTS cũ nguyên vẹn, challenge log và blocker giữ nguyên trong STATE. Hàng rào chống "gate vòng mới xanh sẵn nhờ vết vòng cũ" không nằm ở việc xoá vết nữa mà ở các **cơ chế đếm theo vòng**:

| Cơ chế | Đóng đường lọt nào |
|---|---|
| Gate V vòng ≥2 chỉ đọc `intake/loops/l<N>/` **đúng số vòng** trong STATE | Tài liệu vòng cũ (l2 khi đang vòng 3) không xanh hộ vòng mới; INTERVIEW/intake vòng 1 không được đọc nữa |
| *(intake)* Dòng `Rà lại vòng N: <ngày>` trong `_PROPOSAL.md`, ngày ≥ `Vòng mở` | Kế hoạch lập sẵn từ vòng 1 KHÔNG làm gate mọi vòng xanh sẵn — mở vòng nào phải thật sự đọc lại kế hoạch vòng đó và đối chiếu kết quả vòng trước |
| Mốc `(vòng N)` append vào `DECISIONS.md` — gate chỉ đếm quyết định **dưới mốc cuối** | Quyết định vòng cũ không gánh hộ vòng mới |
| Challenge chỉ tính dòng có ngày ≥ `Vòng mở` (STATE không reset nên log cũ còn đó) | Challenge PASS vòng cũ không gánh hộ vòng mới |
| Mỗi vòng một sổ EXPERIMENTS riêng (`EXPERIMENTS-v<N>.md`, script tạo) | Gate E đòi số liệu của vòng này; số liệu cũ vẫn nằm ngay bên cạnh làm insight |
| Bỏ tick mục `(mỗi vòng)` trong `PRODUCTION-READY.md` + toàn bộ `BACKWARD-COMPATIBILITY-CHECKLIST.md §3` | "Đã kiểm cho tính năng cũ" không tự thành "đã kiểm cho tính năng mới"; hạ tầng (HTTPS, backup…) giữ nguyên |

`repeat.py --go` chỉ làm sổ sách: archive **snapshot** (`PRD/INTERVIEW/PROTOTYPE/DESIGN-SYSTEM/CAPABILITIES-MAP/ROADMAP/sổ EXPERIMENTS của vòng/BC-CHECKLIST/STATE` → `context/archive/vong-N/` — chỉ copy, bản sống giữ nguyên) · sửa STATE **tại chỗ** (Vòng N+1, `Vòng mở: <ngày>`, pha V, ngày D1, bỏ tick §Gate) · tạo `EXPERIMENTS-v<N+1>.md` + `intake/loops/l<N+1>/` · mốc DECISIONS · bỏ tick hai checklist trên · MOVE drop `intake/*.md` gốc vào archive (đường MESH-render chỉ của vòng 1; `intake/design-systems/` và `intake/loops/` ở lại — loops đánh số theo vòng, tự nó là lưu trữ). Ngày chốt PROTOTYPE **giữ nguyên** — tài liệu vòng trong `intake/loops/` là chữ ký của Authority cho vòng mới.

**Legacy là hợp đồng.** Từ vòng 2, AC + luồng lõi + dữ liệu các vòng trước là thứ đã giao cho người dùng thật — mặc định **không được phá**: smoke test vòng cũ đi theo `make test` và phải giữ xanh; migration thuận tương thích (chỉ thêm; đổi/xoá đi hai bước qua hai vòng); dogfood vòng mới đi lại luồng vòng cũ. Chỗ nào bắt buộc phải phá → Authority chốt ở **một trong ba nơi**: file `.md` thả vào `intake/loops/l<N>/` · mục "Legacy được phép phá" trong `intake/loops/l<N>/_PROPOSAL.md` (đường intake) · chốt qua chat ở pha V, meta ghi hộ vào `l<N>/`. Ngoài ba nơi đó thì không có chỗ nào chốt được chuyện phá legacy. Sau khoá scope mới phát hiện buộc phải phá = ngoại lệ "hỏi thật" của §3d, ngang hàng xoá dữ liệu production.

Vòng **chưa từng deploy** (đường intake, vòng chỉ V+I) thì chưa giao gì cho người dùng thật — legacy lúc đó là legacy của vòng đã deploy gần nhất, không phải của vòng liền trước. `guard_bc` chặn đúng lúc deploy nên phép đếm này tự khớp.

Hợp đồng được kiểm bằng máy qua `context/BACKWARD-COMPATIBILITY-CHECKLIST.md`: **sổ hợp đồng** (§1 — API request/response, bảng DB, cache entity, event/message, webhook, tích hợp khác), **luật đổi additive-first từng loại** (§2 — version hoá API, expand→migrate→contract cho DB, nâng version key cache, event-type mới khi đổi nghĩa…), và **checklist rà mỗi vòng** (§3). Gate `P1` vòng ≥2 đếm §3; hook `scripts/guard_bc.py` **chặn thẳng lệnh deploy** khi §3 còn mục chưa tick. `repeat.py --go` giữ nguyên sổ hợp đồng §1, chỉ bỏ tick §3 — vòng nào rà vòng đó.

Nhịp một vòng: *(phỏng vấn)* khoá scope trong 2 tiếng, xong trong 1 tuần — không khoá nổi thì sản phẩm vượt cỡ đường này, xem §7 hoặc chuyển sang đường intake. *(intake)* mỗi vòng tự khai thời lượng trong `_PROPOSAL.md` theo cadence của wave tương ứng; ép mọi wave vào một tuần là ép sai cỡ.

### 1.3 Đường vào pha V — theo vòng

**Vòng 1** có hai đường vào; `/viper-validate` Bước 0 tự nhận diện. Chúng khác nhau ở **nguồn hiểu sản phẩm** và ở **cỡ sản phẩm được phép** (§0) — ba chốt cuối (Authority chốt prototype nếu có UI · challenge pha V · khoá scope) giữ nguyên ở cả hai.

| Vòng 1 | **Đường phỏng vấn** (mặc định) | **Đường intake** |
|---|---|---|
| Kích hoạt | Không có `intake/PRD.md` | `intake/PRD.md` tồn tại, không rỗng — render MESH đã resolve hết `{{…}}` |
| Nguồn hiểu sản phẩm | Phỏng vấn sâu 14 mục, mỗi mục có bằng chứng | Bộ tài liệu Authority thả vào `intake/`: `PRD.md` (bắt buộc) + `ARCHITECTURE.md` / `TECHSTACK.md` / `ROADMAP.md` / `design-systems/<ds>/` (tuỳ chọn) — định dạng đặc tả ở `intake/_*-TEMPLATE.md` |
| `INTERVIEW.md` | 14 khối `Trả lời:` + `Bằng chứng:` | Marker `NGUỒN: INTAKE` (dòng đầu, ngoài comment) + `## Truy vết intake → context` + `## Lỗ hổng & cách xử`. **Marker này quyết định chế độ của cả dự án** — nó ở lại khi file đóng băng, và mọi rẽ nhánh của `gate.py` / `/viper-implement` đọc nó |
| Việc chính | Hỏi cho đủ và sâu (§3a) | **Dịch trung thành** intake → `context/`; tách `PERSONAS.md` + `CAPABILITIES-MAP.md` từ PRD §2–§3; **lập kế hoạch chia vòng** (§1.4) |
| Lỗ hổng thông tin | Hỏi tiếp — không giới hạn số câu | Tìm trong intake → hỏi Authority (vẫn pha V) → tự quyết + 1 dòng `DECISIONS.md` mỗi lỗ |
| Stack | Chọn ở Bước 4, Authority chốt; dựng theo default stack skill | Theo intake `TECHSTACK.md` per-target — **intake thắng default của stack skill**; skill chỉ tham khảo (preset production-ready, forbidden patterns khi không mâu thuẫn); không khớp skill nào → `custom (intake)` |
| Cấu trúc code | Luật #5: một app, scaffold gốc repo | Đa target theo intake ARCHITECTURE — mỗi boundary/experience một thư mục dưới `srcroot/boundaries|web-experiences|mobile-experiences/` (`srcroot/README.md`); root `Makefile` vẫn là hợp đồng 6 lệnh duy nhất, deploy qua root `make deploy` |
| Số AC · persona | 3–7 AC · 2–3 persona | Không trần — AC truy được về `CAPABILITIES-MAP.md`; persona theo intake PRD |
| Prototype | MỘT `prototype/index.html` | `prototype/<experience>/index.html` cho từng experience có UI; mã màn `S<số>` **toàn cục** |
| Design system | Pha V tự quyết token; một bộ cho cả sản phẩm | Có `design-systems/<ds>/tokens.json` → dịch trung thành, hook `guard_ds` chặn bịa/bỏ rơi/lệch. **Nhiều gói là bình thường** — mỗi gói đối chiếu riêng, experience nào mặc gói nào khai ở `ARCHITECTURE §2–§3` |
| Gate V khác biệt | 14 dòng `Bằng chứng:` | `intake/PRD.md` render thật + marker + bảng truy vết + `CAPABILITIES-MAP.md` đã tách + **kế hoạch vòng khớp `_PROPOSAL.md`** |

Sau khi dịch xong, **`context/` là nguồn sự thật** (luật #4) — file trong `intake/` là đầu vào đóng băng, không sửa tay; muốn đổi thì Authority thả bản render mới và chạy lại `/viper-validate` (chỉ khi còn pha V).

**Vòng ≥2 — không phỏng vấn**, `INTERVIEW.md` đóng băng làm hiện vật vòng 1. Nguồn của vòng nằm ở `intake/loops/l<N>/`, nhưng **là cái gì thì khác nhau theo chế độ**:

| | **Phỏng vấn — tài liệu vòng** | **Intake — kế hoạch vòng** |
|---|---|---|
| Kích hoạt | `STATE.md` có `Vòng: N ≥ 2` | như bên trái, cộng marker `NGUỒN: INTAKE` |
| Nguồn hiểu vòng mới | Authority thả ≥1 `.md` vào `l<N>/` mô tả **thêm mới / thay đổi / bỏ đi** (mẫu `_TEMPLATE.md`) | `l<N>/_PROPOSAL.md` — kế hoạch lập ở vòng 1 (§1.4), cộng `.md` Authority thả thêm nếu muốn điều chỉnh |
| Chữ ký Authority | Chính tài liệu vòng — không nghi thức chốt riêng | Đã ký **một lần cho cả kế hoạch** ở vòng 1; từ vòng 2 không phải ký lại |
| Fail-closed nhờ | Thư mục phải có tài liệu thật | Dòng `Rà lại vòng N: <ngày>` ngày ≥ `Vòng mở` — meta phải thật sự rà lại kế hoạch khi mở vòng |
| Insight kèm theo | Sổ EXPERIMENTS vòng trước · `ROADMAP.md` backlog · `DECISIONS.md` | như bên trái, cộng `CAPABILITIES-MAP.md` cột Trạng thái |
| Việc chính | Đọc trọn `l<N>/` → cập nhật PRD (AC mới thay AC cũ) / PERSONAS / ARCHITECTURE / TECHSTACK / PROTOTYPE + DESIGN-SYSTEM nếu tài liệu vòng đụng tới | như bên trái, nguồn là `_PROPOSAL.md`; thêm: cập nhật cột Trạng thái của `CAPABILITIES-MAP.md` và §1 `ROADMAP.md` |
| Prototype | Ngày chốt cũ còn nguyên, không chốt lại; delta UI lớn thì mời bấm thử là khuyến nghị | như bên trái; `UI vòng này: không có màn mới` → gate bỏ qua cả cụm |
| Legacy | Mặc định giữ (§1.2); chỗ phá phải nằm trong tài liệu vòng | như bên trái, hoặc mục "Legacy được phép phá" của `_PROPOSAL.md` |

Cả hai chế độ: gate V vòng ≥2 còn đòi ≥2 quyết định dưới mốc `(vòng N)` và challenge V ngày ≥ `Vòng mở`. Sau khoá scope, `l<N>/` **đóng băng**; muốn đổi ý giữa vòng → `ROADMAP.md` chờ vòng sau. Thư mục đánh số theo vòng nên không cần move đi đâu — gate chỉ đọc đúng `l<N>` của vòng hiện tại.

### 1.4 Kế hoạch vòng — riêng của đường intake

Đường intake nhận **cả một hệ thống đã phân tích xong**, không phải một MVP để thăm dò. Vì vậy việc đầu tiên của pha V vòng 1, sau khi dịch tài liệu, là **cắt hệ thống thành N vòng**: đọc `intake/ROADMAP.md §2` (wave sequence) + `intake/PRD.md §3–§4` (capability × phase) rồi quyết vòng nào giao capability nào, chạm target nào, và **chạy tới pha nào**.

Kế hoạch nằm ở hai chỗ, phải khớp nhau — `gate.py V` vòng 1 đối chiếu:

| Nơi | Nội dung |
|---|---|
| `context/ROADMAP.md §1` | Bảng tổng, mỗi vòng một dòng: phạm vi · pha chạy · phụ thuộc · trạng thái. **Bản sống, nguồn sự thật** (luật #4) |
| `intake/loops/l<N>/_PROPOSAL.md` | Chi tiết một vòng: mục tiêu · capability giao · target · AC dự kiến · UI · legacy được phép phá. Mẫu: `intake/loops/_PROPOSAL-TEMPLATE.md` |

Bốn dòng đầu của `_PROPOSAL.md` là thứ máy đọc:

```
NGUỒN: KẾ HOẠCH VÒNG — lập ở vòng 1 ngày <ISO>, từ intake/ROADMAP.md §2 + intake/PRD.md §3
Pha vòng này: V, I, P
Thời lượng dự kiến: <theo wave cadence>
UI vòng này: có màn mới | không có màn mới
Rà lại vòng <N>: <ISO — ghi khi mở vòng, không ghi trước>
```

**`Pha vòng này` luôn chứa `V, I`** — hai pha đó bắt buộc ở mọi vòng, gate tự thêm vào nếu khai thiếu. Thêm `P` ở vòng deploy, `E` ở vòng đo, `R` ở vòng quyết go/pivot/kill. Vòng không khai thì `gate.py` bỏ qua gate tương ứng và in rõ lý do; `/viper-polish`, `/viper-publish`, `/viper-evaluate` cũng tự dừng ngay ở bước đầu.

Vì sao chỉ V và I bắt buộc: **V** là chỗ duy nhất scope được khoá và challenge được chấm — bỏ V thì vòng đó code không có hợp đồng. **I** là chỗ sản phẩm thật sự tiến lên, và dogfood nằm trong gate I nên chất lượng không rơi tự do. Còn P/E/R phụ thuộc việc **đã có gì đáng deploy chưa**: deploy một wave hạ tầng chưa ai dùng được là nghi thức, và chưa deploy thì không có số liệu để đo hay để quyết.

**Đổi kế hoạch giữa chừng** đi đúng một đường: sửa `ROADMAP.md §1` **và** `_PROPOSAL.md` của vòng liên quan, ghi lý do vào `## Điều chỉnh khi mở vòng` của proposal đó. Authority muốn đổi thì thả `.md` vào `l<N>/` (hoặc nói qua chat ở pha V, meta ghi hộ). Thêm vòng ngoài kế hoạch cũng vậy — thêm dòng ở `ROADMAP.md §1` rồi tạo `_PROPOSAL.md` tương ứng, nếu không thì `repeat.py` mở ra một vòng rỗng và `gate.py V` fail-closed đúng chỗ đó.

---

## 2. Tám luật

1. **Scope khoá sau pha V.** Phát sinh → ghi `ROADMAP.md` backlog, không chèn vào vòng này. Muốn phá luật → 1 dòng `DECISIONS.md` nói rõ đánh đổi.
2. **Sau pha V: toàn quyền, không hỏi lại.** Từ pha I trở đi agent **không dùng AskUserQuestion**. Mơ hồ → tự quyết theo PRD/ARCHITECTURE/TECHSTACK, ghi 1 dòng `DECISIONS.md`, đi tiếp. Chỉ ba trường hợp được dừng (§3d).
3. **Quyết định không hiển nhiên → 1 dòng `DECISIONS.md` trước khi code.** Đây là thứ **thay thế** cho việc hỏi.
4. **Context là nguồn sự thật.** PRD/TECHSTACK/ARCHITECTURE viết trước, code sau. Code lệch tài liệu → sửa tài liệu **cùng commit**.
5. **Cỡ sản phẩm theo đường vào, không có mặc định chung.**
   *(Đường phỏng vấn)* Một app, một DB, một nơi deploy — không micro-service, không hạ tầng nhiều tầng; scaffold thẳng vào gốc repo.
   *(Đường intake)* Cấu trúc theo intake ARCHITECTURE — mỗi boundary/experience một thư mục dưới `srcroot/<nhóm>/` (`boundaries` · `web-experiences` · `mobile-experiences`), root `Makefile` giữ hợp đồng 6 lệnh. Ranh giới ở đây **không phải "một app"** mà là **"đúng danh sách intake"**: không tự đẻ thêm target ngoài `ARCHITECTURE.md §1–§3`, và không gộp hai target lại cho gọn.
6. **Không secret trong code, không bypass test/lint để cho qua.**
7. **Tiếng Việt có dấu cho mọi văn bản người đọc.** Giữ tiếng Anh cho identifier kỹ thuật, API path, schema field, tên lệnh, tên file, tên role, từ chuyên ngành không có bản dịch chuẩn.
8. **Im lặng với Authority, nhưng phải đối kháng với nhau.** Meta challenge agent bằng câu hỏi khó trước khi cho code; và **không báo xong khi chưa tự dùng sản phẩm** (§3).

---

## 3. Điểm mấu chốt — quyền tự quyết sau pha V

Đây là chỗ VIPER **đảo ngược** MESH. MESH coi agent tự quyết là cấm kỵ. VIPER coi việc hỏi lại sau khi Authority đã chốt là ma sát giết mục tiêu "code xong trong ngày 1".

### a. Pha V phải hiểu cho đủ

Pha V có một mục tiêu duy nhất: **hiểu sản phẩm đủ sâu để sau đó không phải hỏi nữa**. Ba đường tới đó, tuỳ chế độ và vòng:

| | Cách hiểu | Chỗ ghi vết |
|---|---|---|
| Vòng 1 — phỏng vấn | Checklist 14 mục dưới đây, mỗi mục có bằng chứng | `INTERVIEW.md` |
| Vòng 1 — intake | **Dịch trung thành** tài liệu MESH-render + vá lỗ hổng + lập kế hoạch vòng (§1.4) | `INTERVIEW.md` (sổ dịch) · `ROADMAP.md §1` · `_PROPOSAL.md` |
| Vòng ≥2 — cả hai | Đọc trọn `intake/loops/l<N>/` + đối chiếu kết quả vòng trước · **không phỏng vấn** | `DECISIONS.md` · `_PROPOSAL.md` dòng `Rà lại vòng N` |

Checklist 14 mục **chỉ áp cho đường phỏng vấn vòng 1**. Đường intake thay nó bằng việc dịch — nhưng các mục intake không nói tới (đăng nhập, thu tiền, dữ liệu mẫu, ngưỡng go/pivot/kill…) vẫn phải được vá theo đúng trình tự "tìm trong intake → hỏi → tự quyết + DECISIONS".

**Vòng ≥2 không phỏng vấn** (§1.3) — phỏng vấn là công cụ mở rộng tư duy lúc khởi đầu; từ vòng 2 dự án đã hình thành, insight nằm ở số liệu và ở kế hoạch. Trình tự: đọc trọn `intake/loops/l<N>/` → đối chiếu sổ EXPERIMENTS vòng trước + `ROADMAP.md` → cập nhật PRD/context theo delta → mơ hồ thì hỏi Authority qua chat (vẫn pha V, meta ghi hộ vào `l<N>/`) hoặc tự quyết + 1 dòng `DECISIONS.md` → challenge V → khoá scope.

Vì sau đó không được hỏi nữa, `/viper-validate` đi kèm **checklist câu hỏi bắt buộc** — đúng những chỗ agent hay vấp giữa chừng:

| # | Phải làm rõ |
|---|---|
| 1 | Pain point cụ thể + ai đang chịu nó (không phải "người dùng nói chung") |
| 2 | Persona (2–3): chân dung, bối cảnh, thiết bị chính + **năng lực mỗi vai được cấp / không được cấp** — đủ lập ma trận vai × hành động (`PERSONAS.md`) |
| 3 | 3–7 tiêu chí chấp nhận (AC) — làm được cái gì thì coi là xong |
| 4 | Out-of-scope tường minh — cái gì **chắc chắn không làm** tuần này |
| 5 | Mô hình dữ liệu lõi + các ca biên (trùng, xoá, sửa, đồng thời) |
| 6 | Đăng nhập: có không, dùng provider nào |
| 7 | Có thu tiền không, tính thế nào |
| 8 | Trạng thái rỗng và trạng thái lỗi hiển thị ra sao |
| 9 | Dữ liệu mẫu lấy từ đâu để dùng thử |
| 10 | Tên sản phẩm / domain / giọng thương hiệu |
| 11 | Deploy ở đâu, môi trường nào |
| 12 | Con số nào quyết định go / pivot / kill ở cuối tuần |
| 13 | Có UI không? Backend-only → marker `KHÔNG CÓ UI` trong `PROTOTYPE.md` và `DESIGN-SYSTEM.md`, bỏ qua mục 15. Có UI → hỏi thêm **phong cách thị giác bằng hiện vật** (app Authority đang dùng thấy dễ nhìn / nhìn là ngợp; sản phẩm dùng ở đâu) → 3 tính từ + neo tham chiếu |
| 14 | **Legacy & tương thích** — checklist này chỉ áp vòng 1, nên ghi `Vòng 1 — chưa có legacy` (từ vòng 2 chuyện phá legacy chốt trong `intake/loops/l<N>/` — xem §1.2) |
| 15 | Có UI → chốt `DESIGN-SYSTEM.md` **trước**: token (màu/chữ/nhịp, mã hex) · cặp tương phản đạt AA · kho component đóng + trạng thái bắt buộc. Rồi dựng **prototype tương tác** (`PROTOTYPE.md §4` — một file ở đường phỏng vấn, một file mỗi experience ở đường intake) **từ token và kho đó**, **dừng lại cho Authority bấm thử**, sửa theo phản hồi (hình thức → sửa token, không sửa tay từng chỗ) tới khi Authority **chốt** — rồi mới được khoá scope |

Hỏi tới khi đủ, **không giới hạn số câu** — nhưng chỉ ở đây.

**Hỏi thế nào** (chống phỏng vấn hời hợt — chi tiết ở `/viper-validate` Bước 2):

- **Hai chế độ**: mục khám phá (pain, persona, ca biên…) hỏi bằng **hội thoại mở** — `AskUserQuestion` chỉ dùng cho mục quyết định có phương án đếm được (stack, auth, deploy). Lựa chọn có sẵn mớm lời; khám phá bằng multiple-choice là nguồn hời hợt số một.
- **Ngôn ngữ của Authority**: Authority là Founder / Product Owner, không phải kỹ sư — hỏi bằng ngôn ngữ business/sản phẩm; term kỹ thuật bắt buộc phải dùng thì giảng giải theo hướng business trước khi hỏi.
- **Bằng chứng bắt buộc**: hỏi về quá khứ cụ thể, không hỏi tương lai giả định; mỗi mục cần ≥1 câu chuyện thật / con số / hiện vật, ghi vào `INTERVIEW.md` ngay trong lúc hỏi; "thường", "nhiều" phải quy ra số.
- **Đọc lại (playback)**: trước khi viết tài liệu, tóm tắt từng mục đọc lại cho Authority xác nhận — hiểu sai bị bắt tại đây, không phải ở pha I.
- **Challenge trước khi khoá scope** (§b): tài liệu không trả lời được câu khó → quay lại nguồn hiểu sản phẩm của chế độ mình đang đi (hỏi tiếp · dịch lại + vá lỗ hổng · đọc lại kế hoạch vòng + kết quả vòng trước).

### b. Đối kháng nội bộ thay cho hỏi Authority

Cắt kênh hỏi thì phải có thứ khác giữ chất lượng, nếu không "toàn quyền" thành "tự tung tự tác".

**Challenge trước khi code.** Trước khi builder viết dòng đầu tiên của một mảng việc lớn, meta ra **một câu hỏi khó dựa trên context thật** — loại chỉ trả lời được nếu đã đọc và hiểu PRD/ARCHITECTURE, không phải câu hỏi kiến thức chung:

- "AC số 3 và quy tắc hoàn tiền mâu thuẫn nhau ở ca nào? Xử ra sao?"
- "Người dùng bấm gửi hai lần trong 200ms thì dữ liệu ra sao? Chỗ nào trong mô hình đang chặn?"
- "Cái gì trong PRD đang **không** thuộc scope tuần này mà bạn vừa định làm?"

Meta chấm **PASS / FAIL**. FAIL → đọc lại context, trả lời lại, **không được code**. Ghi 1 dòng vào `STATE.md` (bảng Challenge log có cột Pha).

Challenge áp cả cho **pha V, trước khi khoá scope**: 3–5 câu hỏi khó nhất về dự án, trả lời **chỉ bằng những gì đã ghi trong tài liệu**. Câu nào không trả lời được là một lỗ — vá theo đúng chế độ đang đi (vòng 1 phỏng vấn: hỏi Authority tiếp, lúc này còn được hỏi · vòng 1 intake: dịch lại phần đó + vá lỗ hổng · vòng ≥2: đọc lại `l<N>/` + kết quả vòng trước) — rồi mới chấm PASS. Gate V bắt dòng challenge này.

**"You eat your own shit."** Không báo xong khi chưa tự dùng. Điều kiện rời pha I (lặp lại ở P):

1. **Meta tự tay dùng sản phẩm ở localhost** — đi hết luồng lõi như người dùng thật, không phải đọc code rồi suy ra là chạy được.
2. **Spawn subagent dùng thử theo 6 góc nhìn**, thao tác thật (skill `viper-browse`), chia
   **HAI ĐỢT, mỗi đợt tối đa 3 vai**:
   · *đợt 1, cần DB sạch* — trạng thái rỗng và lỗi · người mới · **người khó tính về hình thức**;
   · *seed lại* (`deployment/local/`);
   · *đợt 2, cần DB có dữ liệu* — người vội · người phá · màn hình nhỏ.
   Trình duyệt đã riêng cho từng vai (`mcpServers` inline + `--isolated`) nhưng **server dev và
   DB thì chung**, nên thả cả 6 cùng lúc là vai ghi dữ liệu đè lên cảnh vai khác đang nhìn —
   và trạng thái rỗng chết ngay khi có bản ghi đầu tiên.
   Mỗi vai **đóng một persona thật** từ `PERSONAS.md` — lăng kính là *cách dùng*, persona là *ai đang dùng*; vai phá chạy đủ ma trận vai × hành động; vai khó tính đo giao diện **đã render** bằng computed style so với lát token của design system mà experience đó mặc (`ARCHITECTURE.md §2–§3`).
   Phân vai và phân đợt ở `PERSONAS.md §3`.
3. Mỗi phát hiện → xử ngay nếu nhỏ, hoặc ghi `STATE.md` / `ROADMAP.md` nếu ngoài scope.

Lệnh: `/viper-dogfood`.

### c. Không permission prompt trong sandbox dự án

`.claude/settings.json` allow sẵn `Edit` / `Write` / **`Bash` trần** (tên tool trần = allow toàn bộ — liệt kê ~50 prefix lệnh thì vẫn thua thực tế: lệnh ghép, thêm cờ, lệnh chưa liệt kê đều prompt, đo được hơn 1000 lần bấm Yes trong một dự án thật) + `mcp__browser` (trình duyệt dogfood — thiếu rule này thì mỗi lời gọi `browser_*` là một prompt, còn subagent chạy headless bị từ chối im lặng), đặt `defaultMode: acceptEdits` và `enableAllProjectMcpServers: true`.

An toàn nằm ở thứ tự xét rule của Claude Code: **deny → ask → allow**, độ cụ thể không đảo được thứ tự. Vì vậy `git push` / `make deploy` / `vercel`… trong `ask` vẫn dừng hỏi đúng ngoại lệ số 2 dù Bash được allow toàn bộ; `deny` chặn sudo, force-push, đọc `.env`. Thứ giữ agent ở trong repo là phiên làm việc mở tại thư mục dự án (đừng thêm `additionalDirectories`), không phải permission rule.

Riêng `AskUserQuestion` bị chặn bằng **hook** chứ không phải permission: `scripts/guard_ask.py` (PreToolUse) đọc `STATE.md` và chặn khi **một trong ba**: pha ≠ V · ô `Scope khoá` của §Gate đã tick (luật thật của #2 là "sau khoá scope" — pha chỉ là proxy, và lỗi thực chiến phổ biến nhất là agent quên đổi `Pha hiện tại : V → I` rồi hỏi suốt pha I) · dòng `Pha hiện tại:` có nhưng ghi sai định dạng (chặn kèm hướng dẫn sửa về một mã V|I|P|P1|P2|E|R — fail-open ở đây là mở lỗ đúng chỗ luật #2 cần kín nhất). Không có STATE / không có dòng pha thì vẫn fail-open. Mỗi lệnh pha (`/viper-implement`…) mở đầu bằng việc sửa dòng pha — máy chỉ tự đổi hộ ở `repeat.py` (đặt lại V khi mở vòng). Ngoại lệ số 2 vẫn hỏi được bình thường — bằng lời trong chat, và lớp `ask` đã đứng sẵn trước các lệnh hướng ra ngoài.

Hook chặn thứ hai — `scripts/guard_bc.py` (PreToolUse matcher `Bash`) — chỉ soi **lệnh deploy** (`make deploy`, CLI PaaS dạng deploy): vòng ≥2 mà `BACKWARD-COMPATIBILITY-CHECKLIST.md §3` còn mục chưa rà thì chặn, vì deploy phá hợp đồng schema với client/hệ thống ngoài là không thu hồi được (§1.2). Lệnh Bash khác cho qua ngay; `git push` không chặn ở đây — nó đã nằm ở lớp `ask`. Fail-open khi thiếu STATE/checklist: hook an toàn không được chặn nhầm phiên.

Hook chặn thứ ba — `scripts/guard_ds.py` (PreToolUse matcher `Write|Edit|MultiEdit`) — chỉ soi file trong `prototype/` và `context/DESIGN-SYSTEM.md`, chặn bốn lỗi:

| Lỗi | Vì sao chặn cứng |
|---|---|
| Mã màu thô (`#hex`, `rgb()`, `hsl()`) trong prototype, ngoài khối `:root` | Design system chốt TRƯỚC prototype chỉ có tác dụng nếu prototype thật sự lắp từ token. Gõ thẳng `#hex` cho nhanh thì phản hồi "chữ nhỏ quá / màu chìm quá" của Authority lẽ ra sửa MỘT token rồi lan ra mọi màn, nay thành đi sửa tay từng chỗ — và pha I thừa hưởng đúng mớ đó |
| `var(--x)` mà `--x` chưa khai ở `DESIGN-SYSTEM.md §2` | Khai biến mới thẳng trong prototype là dựng design system thứ hai mà không ai biết; bảng §2 thôi là nguồn sự thật |
| *(intake)* Token trong `DESIGN-SYSTEM.md §2` bịa thêm / lệch giá trị so với `intake/design-systems/<ds>/tokens.json` | Gói design system của intake là **hợp đồng** (§1.3), dịch trung thành chứ không "cải tiến" |
| *(intake, nhiều gói)* `prototype/<experience>/…` dùng token của gói **khác** gói mà experience đó mặc | Trộn design system phá hợp đồng của cả hai gói. Hook tra gói qua cột `Design system` ở `ARCHITECTURE §2–§3`; không tra được experience thì fail-open, gate V là backstop |

Cùng triết lý với hai hook trên: `gate.py` bắt được cả bốn lỗi này (và thêm ba lỗi nữa — token của gói bị bỏ rơi, màn khai ở `PROTOTYPE.md §1` mà chưa dựng, và experience chưa khai thuộc design system nào) nhưng gate chỉ **báo** và chỉ chạy khi có người gọi. Fail-open khi chưa chốt design system, khi §2 chưa khai token nào, khi có marker `KHÔNG CÓ UI`, hoặc khi có nhiều gói mà §2 chưa có cột `DS` — chưa có gì để mà theo, hoặc không hiểu chắc, thì không chặn.

**Từ pha I trở đi hook buông hẳn.** `guard_ds` không soi `srcroot/`: mỗi stack một kiểu diễn đạt màu (Tailwind `bg-blue-500`, CSS-in-JS…) nên luật "mã màu thô" ở đó sẽ báo oan và rồi bị tắt. Thứ canh design system trong code là **dogfood** — vai `viper-user-picky` đo trên app đã render (§3b), đúng với mọi stack.

### d. Chỉ ba trường hợp được dừng

| Tình huống | Xử lý |
|---|---|
| Việc **ra ngoài phạm vi đã khoá** và không suy ra được từ PRD | **Không hỏi** — ghi `ROADMAP.md` backlog, đi tiếp phần còn lại |
| Hành động **không đảo ngược được hoặc hướng ra ngoài**: xoá dữ liệu production, tiêu tiền, đăng ký dịch vụ, công bố ra ngoài, đổi DNS, **phá legacy vòng trước chưa được Authority chốt trong tài liệu vòng `intake/loops/l<N>/`** (§1.2) | **Đây là chỗ duy nhất được hỏi thật** |
| **Chặn cứng** sau khi đã tự thử hết cách | Ghi blocker vào `STATE.md`, chuyển sang việc khác, báo gộp cuối buổi |

Subagent **không bao giờ** hỏi Authority — trả về phát hiện + đề xuất, quyền quyết ở phiên chính.

---

## 4. Makefile là hợp đồng lệnh

Mọi stack đều phải cung cấp đúng 6 lệnh này, nhờ vậy quy trình và gate **không phụ thuộc stack**:

```
make dev      # chạy local (app + db)
make check    # lint + typecheck + build
make test     # smoke + luồng quan trọng
make migrate  # DB migration có version
make deploy   # đẩy lên PaaS
make doctor   # kiểm biến môi trường + kết nối, in cái gì thiếu
```

Stack skill trong `.claude/skills/stack-*/` chịu trách nhiệm điền phần thân cho 6 lệnh này ở pha I.

---

## 5. Khu vực context (nguồn sự thật)

| File | Vai trò |
|---|---|
| `context/PRD.md` | Sản phẩm ở lát cắt **vòng hiện tại**: pain point · đối tượng · AC · out-of-scope · 1 success metric · quyết định đã chốt ở pha V. Cấu trúc theo `intake/_PRD-TEMPLATE.md` |
| `context/INTERVIEW.md` | Sổ phỏng vấn pha V **của vòng 1** — 14 mục, mỗi mục trả lời + **bằng chứng** (câu chuyện thật / con số / hiện vật). Đường intake (§1.3): thay bằng marker `NGUỒN: INTAKE` + bảng truy vết + lỗ hổng. **Từ vòng 2 đóng băng** làm hiện vật — gate không đọc nữa, nhưng **marker ở lại và là thứ quyết định chế độ của cả dự án** |
| `context/CAPABILITIES-MAP.md` | Đường intake, **mọi vòng**: bản đồ năng lực tách từ intake PRD §3 — capability × persona × vòng giao, AC của vòng này, phần còn lại nằm đâu. Cũng là nguồn truy vết AC thay cho trần 7 AC. Đường phỏng vấn không dùng |
| `context/archive/ledger/` | Nơi gấp phần sổ đã hết hiệu lực với gate (DECISIONS cũ, challenge log cũ, blocker đã đóng…) — tạo tay theo `/viper-compact`, `scripts/compact.py` chỉ **báo cáo** chứ không ghi |
| `context/archive/vong-N/` | Snapshot mỗi vòng đã đóng (PRD, INTERVIEW, PROTOTYPE, DESIGN-SYSTEM, CAPABILITIES-MAP, ROADMAP, sổ EXPERIMENTS của vòng, BC-CHECKLIST, STATE + drop `intake/` gốc của vòng 1) — `repeat.py` tạo, chỉ copy, không sửa tay |
| `context/PERSONAS.md` | Persona + năng lực được cấp + **ma trận vai × hành động** — spec phân quyền (pha I) và vai đóng khi dogfood |
| `context/DESIGN-SYSTEM.md` | Nguồn sự thật cho hình thức: 3 tính từ + neo · token (màu/chữ/nhịp) · cặp tương phản AA · kho component đóng · khuôn rỗng/lỗi/đang tải. Chốt TRƯỚC prototype; pha I dùng lại nguyên bảng token. Có gói intake → là **bản dịch trung thành** của gói, hook `guard_ds` giữ. **Nhiều design system** (§0 của file): thêm cột `DS`, ánh xạ experience → gói nằm ở `ARCHITECTURE.md §2–§3`. Backend-only: marker `KHÔNG CÓ UI` |
| `context/PROTOTYPE.md` | Bản đồ màn hình · điều hướng · map AC ↔ màn hình · vết Authority chốt. File prototype: một ở đường phỏng vấn, một mỗi experience ở đường intake. Backend-only: marker `KHÔNG CÓ UI` |
| `context/ROADMAP.md` | **§1 kế hoạch vòng** (đường intake: lập ở vòng 1, §1.4) · AC vòng này · backlog — nơi chứa mọi thứ bị scope-lock đẩy ra |
| `context/TECHSTACK.md` | Stack + version chốt **theo target**, trỏ về stack skill đang dùng. Cấu trúc theo `intake/_TECHSTACK-TEMPLATE.md` |
| `context/ARCHITECTURE.md` | Boundary · experience web/mobile (**cột `Design system`** — nguồn ánh xạ duy nhất experience → gói) · sơ đồ · contract giữa target · mô hình dữ liệu · luồng lõi · ranh giới module. Cấu trúc theo `intake/_ARCHITECTURE-TEMPLATE.md`; đường phỏng vấn điền một dòng cho §1–§3 |
| `context/DECISIONS.md` | Append-only. Mỗi quyết định 1 dòng + giả định + đảo ngược được không |
| `context/PRODUCTION-READY.md` | Checklist 4 nhóm, gate của pha P |
| `context/BACKWARD-COMPATIBILITY-CHECKLIST.md` | Vòng ≥2: sổ hợp đồng surface (API/DB/cache/event/webhook/tích hợp) + luật additive-first + checklist rà mỗi vòng — gate `P1` đếm, hook `guard_bc` chặn deploy |
| `context/EXPERIMENTS.md` | Sổ đo vòng 1: giả thuyết → cách đo → số liệu thật → kết luận. Vòng N ≥2 dùng sổ riêng `EXPERIMENTS-v<N>.md` (`repeat.py` tạo) — sổ cũ nguyên vẹn làm insight |
| `context/shared/CONVENTIONS.md` | Quy ước code, phần lớn trỏ về stack skill |
| `context/shared/SECURITY.md` | Baseline bảo mật |
| `context/shared/DEPLOY.md` | PaaS, env vars, migration, rollback |
| `intake/` | Cửa nhận tài liệu từ Authority (§1.3). Vòng 1: drop MESH-render `PRD.md` + tuỳ chọn; `_*-TEMPLATE.md` là đặc tả định dạng. Vòng ≥2: `intake/loops/l<N>/` — tài liệu vòng Authority thả (đường phỏng vấn) hoặc `_PROPOSAL.md` kế hoạch vòng (đường intake, §1.4). Đầu vào đóng băng sau khoá scope — `context/` thắng |
| `intake/loops/l<N>/_PROPOSAL.md` | Đường intake: kế hoạch của vòng N — pha chạy · phạm vi capability · target · UI · legacy được phép phá · dòng `Rà lại vòng N`. Lập ở vòng 1 cho mọi vòng; mẫu `intake/loops/_PROPOSAL-TEMPLATE.md` |
| `srcroot/` | Đường intake: code chia ba nhóm `boundaries/` · `web-experiences/` · `mobile-experiences/`, mỗi target một thư mục con trùng tên với `ARCHITECTURE.md §1–§3`. Đường phỏng vấn không dùng (luật #5) |
| `deployment/` | Cách **chạy** sản phẩm, tách khỏi code. `.env.example` (danh sách TÊN biến cho cả hệ — file env duy nhất được commit) · `local/` (pha I viết vào đây: `docker-compose.yml`, `.env`, seed dữ liệu mẫu). Root `Makefile` trỏ vào đây, không rải artifact ra gốc repo |
| `STATE.md` | Trạng thái sống: pha, ngày, gate, challenge log, blocker |

---

## 6. Production Ready — 4 nhóm (cả 4 bắt buộc trước khi rời pha P)

1. **Nền kỹ thuật** — env/secret tách khỏi code · migration có version · health check · error tracking · structured log · backup DB
2. **Auth + bảo mật** — managed auth · validate input · rate limit · HTTPS · không hardcode secret
3. **CI/CD + test tối thiểu** — push là deploy · smoke test + test luồng tiền/dữ liệu quan trọng · **không đặt mục tiêu coverage %**
4. **Đo phản ứng thị trường** — analytics + event tracking cho hành vi then chốt · kênh feedback · con số quyết định go/pivot/kill

Mục gắn `(sau deploy)` chỉ tick được khi production đã sống — xem §1.1 để biết mục nào thuộc gate `P1`, mục nào thuộc `P2`.

Chi tiết từng mục: `.claude/skills/shared-production-ready/SKILL.md`.

---

## 7. Đường nâng cấp sang MESH

Khi sản phẩm vượt ngưỡng ở §0 (nhiều hơn 1 service · đội nhiều người · cần contract giữa các phần), `context/` ánh xạ thẳng sang MESH:

| VIPER | MESH |
|---|---|
| `context/PRD.md` | `PRD.md` (T0) + `_discovery/capability-map.md` |
| `context/ARCHITECTURE.md` | `SYSTEM-ARCHITECTURE.md` + `<target>/solution/HLD.md` |
| `context/TECHSTACK.md` | `TECHSTACK.md` + `ADR-D3-001..003` |
| `context/DECISIONS.md` | `Execution/tracking/decisions.md` + `solution/decisions/ADR-*.md` |
| `context/ROADMAP.md` | `ROADMAP.md` + `Plan/WAVE-SEQUENCE.md` |
| `context/PRODUCTION-READY.md` | `_shared/{security,observability,release}-policy.md` |

Không có đường ngược lại — MESH không hạ cấp về VIPER.

---

## 8. Bản hiện tại — v1.9 (2026-08-12)

**Framework không giữ tham chiếu ngược.** Không có lịch sử version ở đây: dự án đọc file
này để biết luật **đang** ra sao, không phải để biết luật từng ra sao. Nâng version thì
viết lại mục này cho khớp bản mới, đừng append thêm dòng.

Bản 1.9 đứng trên sáu cơ chế:

| Cơ chế | Ở đâu |
|---|---|
| **Hai đường vào, ràng buộc khác nhau** — phỏng vấn (một tuần, một app, 3–7 AC, 2–3 persona) vs intake (hệ thống lớn chia vòng, đa target, không trần AC/persona, tự khai thời lượng). Luật của đường này không áp cho đường kia | §0 · §1.3 · luật #5 |
| **Vòng, đếm theo vòng thay cho reset** — mốc `(vòng N)` ở DECISIONS · challenge tính từ `Vòng mở` · sổ `EXPERIMENTS-v<N>` riêng · gate V chỉ đọc đúng `l<N>` | §1.2 |
| **Kế hoạch vòng (chỉ intake)** — pha V vòng 1 cắt hệ thống thành N vòng, ghi `ROADMAP.md §1` + `intake/loops/l<N>/_PROPOSAL.md`; mỗi vòng khai `Pha vòng này`: **V và I bắt buộc**, P/E/R chỉ ở vòng Authority chốt | §1.4 |
| **Ba hook chặn cứng** — `guard_ask` (hỏi ngoài pha V) · `guard_bc` (deploy khi còn nợ tương thích ngược) · `guard_ds` (prototype/design system lệch bản đã chốt, kể cả mượn token của gói khác) | §3c |
| **Nhiều design system, canh theo experience** — mỗi gói `intake/design-systems/<ds>/` đối chiếu RIÊNG (khoá `(ds, token)`, hết hợp nhất); ánh xạ experience → gói ở `ARCHITECTURE §2–§3`; `prototype/<exp>/` chỉ được dùng lát token của gói mình. Một design system thì không phải khai gì thêm | §5 · §3c |
| **Vệ sinh tài liệu** — `scripts/compact.py` báo cáo rác tích tụ, mục mồ côi, và **dòng neo không được đụng**; gấp bằng tay vào `context/archive/ledger/` theo `/viper-compact`. Chỉ đọc, không có `--go` | §5 |

Thứ giữ chất lượng khi cắt kênh hỏi Authority: challenge trước khi code, dogfood trước
khi báo xong (§3b), và gate của từng pha (§1.1) — gate chỉ **báo**, ba hook trên mới chặn.
