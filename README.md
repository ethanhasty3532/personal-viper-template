> Bản mẫu sạch cho dự án cá nhân. Bắt đầu tại [START-HERE.md](START-HERE.md).

# VIPER — template

Quy trình **solo, một người quyết tất**, dựng sản phẩm production-ready. Có **hai đường vào**, cho hai bối cảnh khác nhau:

| **Đường phỏng vấn** | **Đường intake** |
|---|---|
| Founder/PO có một ý tưởng → test thị trường trong **một tuần** | Đã có bộ tài liệu MESH-render → giao **một hệ thống lớn, chia thành nhiều vòng** chạy dần |
| 1 app, 1 DB, 1 nơi deploy · 3–7 AC · 2–3 persona | Đa target `srcroot/{boundaries,web-experiences,mobile-experiences}/` · AC và persona theo tài liệu, không trần |
| Mỗi vòng chạy trọn V-I-P-E-R | **V và I bắt buộc mọi vòng**; P/E/R chỉ ở vòng Authority chốt |
| Pha V = phỏng vấn sâu 14 mục | Pha V = dịch trung thành + lập kế hoạch chia vòng |

```
V ──► I ──► P ──► E ──► R
Validate  Implement  Polish&Publish  Evaluate  Repeat

phỏng vấn: D1 sáng   D1 còn lại   D2            D2–D5      cuối tuần
           (2–3 giờ) (bắt buộc)   (khuyến nghị) (tuỳ chọn)
intake:    mọi vòng  mọi vòng     ── chỉ ở vòng khai trong _PROPOSAL.md ──
```

**Đường phỏng vấn: ngày 1 code xong, chạy được ở local.** Bốn ngày còn lại là tuỳ chọn — deploy, tối ưu, fix bug, đo phản ứng. Release nằm trong tuần.
**Đường intake: mỗi vòng tự khai thời lượng** theo wave cadence của tài liệu; ràng buộc "một tuần" không áp.

Ràng buộc của đường phỏng vấn là ràng buộc **tốc độ của bối cảnh một tuần**, không phải luật chung của VIPER — đừng mang chúng áp sang đường intake (`VIPER.md §0`).

VIPER chắt lọc từ [MESH v4.6](../{{PROJECT-CODE}}-MESH) — giữ *context là nguồn sự thật · quyết định phải có vết · gate trước khi đi tiếp*; bỏ đa Authority, contract signing nhiều đội, wave orchestration nhiều repo. Hook chặn giữ đúng ba: `AskUserQuestion` ngoài pha V, deploy khi vòng ≥2 còn nợ tương thích ngược, và ghi prototype/design system lệch bản đã chốt.

---

## Khởi tạo dự án mới

```bash
python3 scripts/bootstrap.py <project-code> \
  --name "Tên dự án" \
  --authority "Tên bạn <email@example.com>"

# xem trước, không ghi gì:
python3 scripts/bootstrap.py <project-code> --dry-run
```

Script **copy** template ra thư mục mới (mặc định `../<project-code>`), thay placeholder, `git init` + commit đầu. Template giữ nguyên, dùng lại được cho dự án sau.

```bash
cd ../<project-code>
claude
/viper-validate       # bắt đầu
```

Yêu cầu:

| Cần | Để làm gì | Bắt buộc? |
|---|---|---|
| **Python 3.9+** · git | `bootstrap.py`, `gate.py` — Python thuần, thư viện chuẩn, chạy trên macOS / Linux / Windows | Có |
| **Node.js 18+** (kèm `npm`) | Skill `viper-browse` mở trình duyệt thật cho `/viper-dogfood` (Playwright MCP, tải khi chạy lần đầu) | Có, vì luật #8 bắt dogfood |
| Runtime của stack đã chốt (+ Docker nếu dùng DB local qua compose — xem stack skill §2) | Chạy sản phẩm | Từ pha I |

Trên Windows dùng `python` thay cho `python3`:

```powershell
python scripts\bootstrap.py <project-code> --name "Tên dự án"
python scripts\gate.py
```

`make` không có sẵn trên Windows — cài qua [Chocolatey](https://chocolatey.org) (`choco install make`), hoặc chạy thẳng lệnh của stack ghi trong `.claude/skills/stack-<tên>/SKILL.md §4`.

---

## Sửa template thì chạy cái này

```bash
python3 scripts/selftest.py             # bộ phép kiểm tự động, vài giây
python3 scripts/selftest.py --browser   # kiểm luôn Playwright MCP (cần mạng, chậm)
```

Nó bootstrap một dự án nháp rồi đi hết V → I → P1 → P2 → E → R, kiểm cả hook, permission, frontmatter agent và `.gitignore`. Template này từng nhiều lần "review tay thấy ổn" mà vẫn còn bug — bộ tự kiểm sinh ra để thay việc dò tay đó.

---

## Điểm khác biệt cốt lõi

**Hỏi dồn một lần ở pha V, sau đó agent toàn quyền trong thư mục code và không hỏi lại.**

MESH coi agent tự quyết là cấm kỵ (sàn câu hỏi, confidence gate, hook chặn write). VIPER đảo ngược: Authority đã chốt xong rồi thì mọi câu hỏi tiếp theo là ma sát — thứ giết mục tiêu "code xong trong ngày 1".

Cài đặt bằng bốn thứ, không phải bằng lời khuyên:

1. **Pha V hiểu cho đủ và cho sâu** — hai đường tới đó, ba chốt cuối (Authority chốt prototype nếu có UI · challenge pha V · khoá scope) giữ nguyên ở cả hai.

   *Đường phỏng vấn*: `/viper-validate` mang checklist 14 mục bắt buộc (kèm persona + năng lực từng vai, phong cách thị giác hỏi bằng hiện vật, legacy & tương thích), hỏi không giới hạn số câu, nhưng chỉ ở đây. Chống hỏi hời hợt bằng cơ chế, không bằng lời dặn: hai chế độ hỏi (khám phá = hội thoại mở, quyết định = AskUserQuestion), **bằng chứng bắt buộc** ghi `INTERVIEW.md` (gate V kiểm 14 dòng), ngôn ngữ business cho Founder/PO, đọc-lại xác nhận, **challenge pha V** trước khi khoá scope.

   *Đường intake* (`VIPER.md §1.3–§1.4`): Authority thả bộ tài liệu MESH-render vào `intake/` (`PRD.md` là trigger), meta **dịch trung thành** sang `context/` + tách `PERSONAS.md` và `CAPABILITIES-MAP.md`, không phỏng vấn lại. Rồi **lập kế hoạch chia vòng**: đọc wave sequence + capability map, cắt hệ thống thành N vòng, ghi `ROADMAP.md §1` và sinh `intake/loops/l<N>/_PROPOSAL.md` cho từng vòng — mỗi vòng khai `Pha vòng này` (V+I bắt buộc, P/E/R theo Authority chốt). Intake `TECHSTACK.md` thắng default của stack skill; sản phẩm đa target (`srcroot/<nhóm>/<tên>/`); AC/persona không trần nhưng AC phải truy được về capability.

   Sản phẩm có UI → chốt **design system** (`context/DESIGN-SYSTEM.md`: token · tương phản gate tự tính theo WCAG AA · kho component đóng) rồi dựng **prototype tương tác** từ đúng token đó, dừng cho Authority bấm thử và **chốt** rồi mới khoá scope; backend-only bỏ qua bằng marker `KHÔNG CÓ UI`. Prototype phải thật sự lắp từ token — hook `scripts/guard_ds.py` chặn mã màu thô ngoài `:root`, token chưa khai, và (đường intake) token bịa/lệch so với gói `intake/design-systems/<ds>/tokens.json`.
2. **Từ pha I cấm `AskUserQuestion`** — thay bằng "giả định thay vì câu hỏi": tự quyết, ghi một dòng `context/DECISIONS.md`, đi tiếp. Authority review theo lô cuối buổi. Cấm bằng **hook** `scripts/guard_ask.py` (PreToolUse chặn cứng), không chỉ bằng lời dặn — thực chiến cho thấy lời dặn trôi sau compact.
3. **`.claude/settings.json` allow sẵn** Edit / Write / **Bash toàn bộ** + `mcp__browser` (trình duyệt dogfood), `defaultMode: acceptEdits` → không permission prompt trong sandbox dự án. Bản 1.0 liệt kê ~50 prefix lệnh và vẫn dính hơn 1000 prompt/dự án. An toàn nhờ thứ tự xét **deny → ask → allow**: deploy/push/publish trong `ask` vẫn dừng hỏi đúng chỗ.
4. **Chỉ ba trường hợp được dừng**: ngoài scope (→ ghi ROADMAP, không hỏi) · không đảo ngược được hoặc hướng ra ngoài (→ đây là chỗ duy nhất hỏi thật) · chặn cứng (→ ghi blocker, làm việc khác).

Có một lỗ hổng ở cách cài đặt này: **compact**. Bản tóm tắt giữ được *đang làm gì* nhưng làm phẳng *đang bị cấm gì* — mà bốn thứ trên đều thuộc loại thứ hai. Pha I chắc chắn chạm compact.

Vá bằng hook `SessionStart` matcher `compact`: ngay sau khi nén, [scripts/reanchor.py](scripts/reanchor.py) đọc lại 8 luật + `STATE.md` + AC **từ file** rồi nhồi vào context (~500 token). Meta không phải nhớ, vì luật vốn nằm trong file.

Đây là **giả thuyết chưa được chứng minh**, nên script tự ghi log mỗi lần chạy và có sẵn cách đo:

```bash
python3 scripts/reanchor.py --audit    # compact mấy lần, sau mỗi lần có phá luật không
```

Bù lại việc cắt kênh hỏi, VIPER bắt **đối kháng giữa các agent**:

- **Challenge trước khi code** — meta ra một câu hỏi khó dựa trên context thật, chấm PASS/FAIL. FAIL thì đọc lại, không được code.
- **"You eat your own shit"** — không báo xong khi chưa tự dùng. Meta tự tay dùng ở localhost + 6 subagent dùng thử theo 6 góc nhìn, chạy **hai đợt tối đa 3 vai** (`/viper-dogfood`) — trình duyệt thì riêng nhưng DB dùng chung, thả cả 6 cùng lúc là vai này đè cảnh vai kia.

---

## Cấu trúc

```
VIPER.md                    policy T0 — 5 pha, 8 luật, gate
CLAUDE.md                   router đọc mỗi phiên
STATE.md                    pha hiện tại, gate, challenge log, blocker
Makefile                    hợp đồng lệnh: dev/check/test/migrate/deploy/doctor

intake/                     cửa nhận tài liệu từ Authority (VIPER.md §1.3)
├── README.md               hợp đồng thả file: PRD.md bắt buộc (trigger vòng 1) + 4 loại tuỳ chọn
├── _*-TEMPLATE.md          đặc tả định dạng render (copy nguyên văn, không substitute)
├── design-systems/         gói design system — HỢP ĐỒNG hình thức, dịch trung thành:
│   └── <ds-name>/          DESIGN-SYSTEM.md · tokens.json · components/<tên>.md
└── loops/l<N>/             vòng ≥2 (không phỏng vấn). Phỏng vấn: tài liệu vòng Authority thả
                            (mẫu _TEMPLATE.md). Intake: _PROPOSAL.md — kế hoạch vòng lập ở
                            vòng 1, khai `Pha vòng này` (mẫu _PROPOSAL-TEMPLATE.md)

srcroot/                    đường intake: code chia ba nhóm (README bên trong)
├── boundaries/<tên>/       backend boundary        ← ARCHITECTURE §1
├── web-experiences/<tên>/  frontend web            ← ARCHITECTURE §2
└── mobile-experiences/<tên>/  frontend mobile      ← ARCHITECTURE §3

deployment/                 cách CHẠY sản phẩm, tách khỏi code (README bên trong)
├── .env.example            danh sách TÊN biến cho cả hệ — file env duy nhất được commit
└── local/                  pha I viết vào đây: docker-compose.yml · .env · seed dữ liệu mẫu

context/                    khu vực tuân thủ — nguồn sự thật
├── PRD.md                  pain point · đối tượng · AC · out-of-scope · success metric
├── INTERVIEW.md            sổ phỏng vấn pha V vòng 1 — 14 mục có bằng chứng; đường intake: marker NGUỒN: INTAKE + truy vết; từ vòng 2 đóng băng
├── CAPABILITIES-MAP.md     đường intake (mọi vòng): capability × persona × vòng giao — nguồn truy vết AC
├── PERSONAS.md             persona + năng lực được cấp + ma trận vai × hành động
├── DESIGN-SYSTEM.md        token · tương phản AA · kho component — chốt TRƯỚC prototype
├── PROTOTYPE.md            bản đồ màn hình · map AC ↔ màn hình · vết Authority chốt prototype
├── archive/vong-N/         snapshot mỗi vòng đã đóng — repeat.py tạo khi mở vòng mới
├── ROADMAP.md              §1 kế hoạch vòng (intake) · AC vòng này · backlog
├── TECHSTACK.md            stack chốt + version, theo target
├── ARCHITECTURE.md         boundary · experience · topology · contract · dữ liệu · luồng lõi
├── DECISIONS.md            append-only — thứ THAY THẾ cho việc hỏi
├── PRODUCTION-READY.md     checklist 4 nhóm — gate pha P
├── BACKWARD-COMPATIBILITY-CHECKLIST.md   vòng ≥2: sổ hợp đồng surface + luật additive-first — gate P1 đếm, hook guard_bc chặn deploy
├── EXPERIMENTS.md          giả thuyết → số liệu → go/pivot/kill (sổ vòng 1; vòng N ≥2: EXPERIMENTS-v<N>.md)
└── shared/                 CONVENTIONS · SECURITY · DEPLOY

.mcp.json                   trình duyệt cho phiên chính (Playwright MCP)

prototype/index.html        prototype tương tác một file — dựng ở pha V (chỉ dự án có UI)

.claude/
├── settings.json           toàn quyền trong sandbox: Bash trần + mcp__browser · ask chặn hướng-ra-ngoài
├── commands/               9 slash command
├── agents/                 6 vai dùng thử (đóng persona) + 3 vai soi kỹ thuật
└── skills/                 viper · viper-browse · shared-production-ready · 5 stack · addon-graphql

scripts/
├── bootstrap.py            tạo dự án mới từ template          ← template only
├── gate.py                 kiểm gate từng pha (chỉ báo, không chặn)
├── guard_ask.py            hook: chặn AskUserQuestion ngoài pha V
├── guard_bc.py             hook: chặn deploy khi vòng ≥2 còn nợ tương thích ngược
├── guard_ds.py             hook: chặn prototype/design system lệch bản đã chốt
├── reanchor.py             hook: nhồi lại luật sau compact · `--audit` để đo hiệu quả
├── repeat.py               đóng vòng N, mở vòng N+1 — archive snapshot + sổ sách theo vòng (không reset)
└── selftest.py             chạy trọn quy trình trên dự án nháp ← template only
```

**`← template only`** = không copy sang dự án. Ba thứ ở lại template: `bootstrap.py` (dự án không sinh dự án khác), `selftest.py` (kiểm chính template), và `README.md` này — dự án nhận một README của riêng nó. `bootstrap.py` luôn chạy **từ thư mục template**, nên bỏ nó khỏi dự án không ảnh hưởng gì.

```
```

---

## Slash command

| Lệnh | Pha | Việc |
|---|---|---|
| `/viper-validate` | V | Phỏng vấn gộp **hoặc** dịch tài liệu intake + lập kế hoạch chia vòng → PRD + persona + stack + kiến trúc + design system + prototype (Authority chốt) + khoá scope · **nơi duy nhất được hỏi** |
| `/viper-implement` | I | Challenge → scaffold → luồng lõi → chạy local |
| `/viper-dogfood` | I, P | Tự dùng + 6 subagent dùng thử (2 đợt × 3 vai) · **bắt buộc trước khi báo xong** |
| `/viper-polish` | P | Production-ready 4 nhóm + subagent soi bug/viết test · *(intake)* chỉ ở vòng khai `P` |
| `/viper-publish` | P | Deploy PaaS + smoke test + thử rollback · *(intake)* chỉ ở vòng khai `P` |
| `/viper-evaluate` | E | Đọc số liệu, thu phản hồi, chọn một việc, đo lại · *(intake)* chỉ ở vòng khai `E` |
| `/viper-repeat` | R | Go/pivot/kill từ số liệu (vòng có chạy E) · đóng vòng, archive, mở vòng mới — legacy vòng trước là hợp đồng |
| `/viper-status` | mọi pha | Đang ở đâu, đường vào nào, vòng này chạy pha gì, thiếu gì |
| `/viper-decide` | mọi pha | Ghi một dòng DECISIONS.md |

---

## Kho stack

Skill pack dạng text + lệnh scaffold chính chủ — **không giữ boilerplate code**, nên không bao giờ lỗi thời.

| Skill | Khi nào | Deploy |
|---|---|---|
| `stack-nextjs-fullstack` | Web app fullstack — nhanh nhất cho MVP 1 ngày | Vercel + Neon |
| `stack-nestjs-react` | Cần API riêng ngay từ đầu (mobile/đối tác dùng chung) | Railway / Render |
| `stack-fastapi` | Sản phẩm dính AI/LLM hoặc data | Railway / Fly.io |
| `stack-go` | Cần hiệu năng, binary gọn | Fly.io / Render |
| `stack-spring-boot` | Đội sẵn có Java, hoặc ràng buộc JVM | Render / Railway |
| `addon-graphql` | Lắp lên NestJS hoặc Next.js khi client cần query linh hoạt | — |

Mỗi skill có cùng khung 8 mục: khi nào chọn/không chọn · scaffold · cấu trúc thư mục · 6 lệnh Makefile · preset production-ready · deploy · forbidden patterns · snippet then chốt.

Thêm stack mới: copy khung 8 mục của `stack-nextjs-fullstack`, viết cho stack của mình.

---

## Production Ready — 4 nhóm

Đây là thứ phân biệt "sản phẩm 1 tuần" với "đồ dùng rồi vứt".

Pha P có **hai** gate: `P1` (mọi mục làm được khi chưa có production → được deploy lần đầu) và `P2` (cả 4 nhóm xanh đủ, production sống, đã thử rollback → rời pha P). Bốn mục gắn `(sau deploy)` — backup · HTTPS · push-là-deploy · analytics đang đếm — nằm ở `P2` vì chúng cần production tồn tại trước.

1. **Nền kỹ thuật** — env/secret · migration có version · health check · error tracking · structured log · backup (đã thử khôi phục)
2. **Auth + bảo mật** — managed auth · validate ở server · rate limit · HTTPS · **phép thử phân quyền A↛B**
3. **CI/CD + test tối thiểu** — push là deploy · smoke test luồng lõi · test luồng tiền/dữ liệu · không đuổi coverage %
4. **Đo phản ứng thị trường** — analytics · event tracking · kênh feedback · ngưỡng go/pivot/kill ghi trước khi nhìn số

---

## Khi nào KHÔNG dùng VIPER

Chung cho cả hai đường vào:

| Hợp | Không hợp |
|---|---|
| Một người quyết tất (solo Authority) | Nhiều Authority sign-off chéo |
| Sai thì làm lại rẻ | Sai là mất tiền/dữ liệu ở quy mô lớn |
| Sản phẩm production-ready thật | Cần contract signing + wave orchestration nhiều đội, nhiều repo |

Riêng **đường phỏng vấn** thêm hai ràng buộc: 1 app / 1 DB / 1 nơi deploy, và phạm vi khoá được trong 2 tiếng. Vượt ngưỡng đó:

- **Đã có tài liệu phân tích** (MESH-render) → đi **đường intake**, đó chính là chỗ nó sinh ra để giải quyết: hệ thống nhiều service, chia vòng chạy dần.
- **Chưa có tài liệu**, phạm vi còn phải khảo sát nhiều tuần → dùng MESH. Đường nâng cấp và bảng ánh xạ tài liệu: `VIPER.md §7`.
