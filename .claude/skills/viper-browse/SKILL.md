---
name: viper-browse
description: >
  Duyệt web thật để dùng thử sản phẩm VIPER ở localhost hoặc production — mở trang, bấm, gõ, chụp màn hình,
  đọc lỗi console và lời gọi mạng. Chạy bằng Playwright MCP (@playwright/mcp), khai ngay trong template nên
  không phụ thuộc công cụ ngoài. Nạp skill này khi chạy /viper-dogfood, khi cần kiểm một luồng bấm được thật
  hay không, hoặc khi đóng vai người dùng thử (viper-user-*). Gồm: cách gọi, 24 tool có sẵn, công thức cho
  từng vai dogfood (màn hình nhỏ, mạng chậm, gửi hai lần, nhiều tab), và cách chứng minh mình đã dùng thật.
---

# viper-browse — duyệt web để dùng thử thật

> Luật #8 nói **không báo xong khi chưa tự dùng**. Skill này là công cụ để "dùng" nghĩa là dùng thật:
> mở trình duyệt, bấm, nhìn màn hình. Đọc code rồi suy ra "chắc chạy được" **không tính**.

## 1. Chạy bằng gì

Playwright MCP (`@playwright/mcp`) — bản chính chủ của Playwright. Template khai sẵn ở hai nơi:

| Nơi khai | Dùng cho | Kiểu |
|---|---|---|
| `.mcp.json` ở gốc repo | Phiên chính (meta tự tay dùng) | dùng chung cả phiên |
| `mcpServers` trong frontmatter mỗi `viper-user-*` | 6 vai dùng thử | **inline — mỗi agent một trình duyệt riêng** |

Khai inline là có chủ ý: server inline được bật khi subagent bắt đầu và tắt khi nó xong, nên **các vai chạy song song mà không giẫm chân nhau**. Nếu để tất cả trỏ chung một server thì chúng tranh nhau một tab — người này bấm, người kia mất trang.

Lưu ý: trình duyệt riêng **không** làm dữ liệu riêng. Server dev và DB vẫn dùng chung, nên vai ghi dữ liệu vẫn đè lên cảnh vai khác đang nhìn — đó là lý do `/viper-dogfood` chạy **hai đợt, mỗi đợt tối đa 3 vai**, không phải cả 6 cùng lúc.

Không cần cài gì trước. Lần đầu chạy, npm tải gói và Playwright tải Chromium (vài trăm MB, chỉ một lần).

## 2. Bốn tool dùng nhiều nhất

| Tool | Việc |
|---|---|
| `browser_navigate` | Mở URL. **Luôn vào từ trang đầu**, không nhảy thẳng vào URL bên trong |
| `browser_snapshot` | Đọc nội dung trang dạng cây accessibility — đây là "nhìn màn hình". Gọi sau mỗi thao tác |
| `browser_click` · `browser_type` · `browser_fill_form` | Bấm và gõ |
| `browser_take_screenshot` | Bằng chứng cho báo cáo, và là cách bắt lỗi bố cục |

**Hai điều dễ vấp, đã kiểm bằng cách chạy thật:**

1. `browser_click` / `browser_type` nhận **`target`**, không phải `ref`. `target` ăn cả **ref lấy từ snapshot** (`e4`) lẫn **CSS selector** (`#them`, `button[type=submit]`) — selector thường nhanh hơn vì khỏi phải snapshot trước. Trường `element` chỉ là mô tả cho người đọc.
2. `browser_navigate` **không trả nội dung trang trong phản hồi** — nó ghi ra `.playwright-mcp/page-*.yml` rồi trả đường dẫn. Muốn thấy trang thì `Read` file đó, hoặc gọi thẳng `browser_snapshot` (tool này trả inline). Thư mục `.playwright-mcp/` đã nằm trong `.gitignore`, đừng commit.

Còn lại: `browser_resize` · `browser_press_key` · `browser_navigate_back` · `browser_tabs` · `browser_hover` · `browser_drag` · `browser_drop` · `browser_select_option` · `browser_file_upload` · `browser_handle_dialog` · `browser_wait_for` · `browser_find` · `browser_console_messages` · `browser_network_requests` · `browser_network_request` · `browser_evaluate` · `browser_run_code_unsafe` · `browser_close`.

**`browser_snapshot` hơn `browser_take_screenshot` khi cần biết trang có gì** — nó trả về text đọc được kèm ref để bấm, không phải ảnh phải đoán.

## 3. Công thức cho từng vai dogfood

### Màn hình nhỏ (`viper-user-mobile`)
Frontmatter đã đặt `--viewport-size 390,844`. Đổi cỡ giữa chừng:
```
browser_resize  width=360 height=640     # máy nhỏ
browser_resize  width=844 height=390     # xoay ngang
```

### Mạng chậm / mất mạng / API lỗi (`viper-user-edge`)
Dùng `browser_run_code_unsafe` để chạy thẳng Playwright:
```js
// mất mạng
await page.context().setOffline(true);
// chặn một API cụ thể, xem UI hiện gì
await page.route('**/api/**', r => r.abort());
// mạng chậm
const c = await page.context().newCDPSession(page);
await c.send('Network.emulateNetworkConditions',
  { offline:false, latency:400, downloadThroughput:400*1024/8, uploadThroughput:400*1024/8 });
```
Rồi `browser_console_messages` và `browser_network_requests` để xem lỗi thật sự là gì.

### Gửi hai lần, bấm nhanh, nhiều tab (`viper-user-rushed`)
```js
// hai lần trong ~50ms — thứ tay người không làm được nhưng mạng lag thì có
await Promise.all([ page.click('#submit'), page.click('#submit') ]);
```
`browser_tabs` mở tab thứ hai cùng một trang · `browser_navigate_back` cho nút quay lại.

### Nhập bậy (`viper-user-breaker`)
`browser_type` với chuỗi 10.000 ký tự, emoji, `<script>alert(1)</script>`, `'; DROP TABLE x;--`, số âm.
Sau mỗi lần: `browser_snapshot` xem có hiện ra **như chữ thường** không, `browser_console_messages` xem có lỗi, `browser_network_requests` xem server trả mã gì.

Phép thử phân quyền A↛B: đăng nhập A tạo bản ghi → `browser_navigate` tới URL bản ghi đó khi đang là B → phải bị chặn.

### Người mới (`viper-user-newbie`)
Không dùng tool đặc biệt. Chỉ `browser_navigate` vào trang đầu rồi `browser_snapshot` — và **đọc như người chưa biết gì**. Đừng dùng kiến thức về code để đoán ra cách dùng; mất vai là mất giá trị lượt thử.

### Khó tính về hình thức (`viper-user-picky`)

Vai này **đo**, không nhìn. `browser_evaluate` gom giá trị thật đang render trên màn:

```js
() => {
  const seen = new Map();                       // "prop|giá trị" → selector đầu tiên gặp
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;         // bỏ phần tử không hiển thị
    const cs = getComputedStyle(el);
    const sel = el.tagName.toLowerCase()
      + (el.id ? '#' + el.id : '')
      + (el.className && typeof el.className === 'string'
         ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
    for (const p of ['color', 'background-color', 'border-color', 'font-family',
                     'font-size', 'padding', 'gap', 'border-radius', 'box-shadow']) {
      const v = cs.getPropertyValue(p);
      if (!v || v === 'none' || v === 'rgba(0, 0, 0, 0)' || v === '0px') continue;
      const k = p + '|' + v;
      if (!seen.has(k)) seen.set(k, sel);
    }
  }
  return [...seen].map(([k, sel]) => k + ' @ ' + sel).sort();
}
```

Trả về **tập giá trị thật + selector đầu tiên dùng nó** — đối chiếu thẳng với lát token `DESIGN-SYSTEM.md §2`. Giá trị nào không có trong lát là phát hiện; giá trị thuộc gói design system khác là **trộn design system**, nặng hơn.

Tương phản thì đọc cặp chữ/nền của đúng phần tử đang nghi:

```js
() => {                                          // nền thật: leo lên tới tổ tiên có nền đục
  const el = document.querySelector('.canh-bao');
  let bg = 'rgba(0, 0, 0, 0)', n = el;
  while (n && bg === 'rgba(0, 0, 0, 0)') { bg = getComputedStyle(n).backgroundColor; n = n.parentElement; }
  return { fg: getComputedStyle(el).color, bg, size: getComputedStyle(el).fontSize };
}
```

Ép hiện trạng thái component: `browser_hover` cho hover · bấm submit rồi `browser_snapshot` ngay để bắt "đang gửi" · `page.route('**/api/**', r => r.abort())` cho khuôn lỗi (§5).

## 4. Chứng minh đã dùng thật

Mọi phát hiện phải nêu được **thao tác cụ thể** và **thứ thấy trên màn hình**. Ba thứ này là bằng chứng:

```
browser_snapshot          → trích đúng đoạn text/nhãn đã thấy
browser_take_screenshot   → ảnh chỗ hỏng
browser_console_messages  → lỗi JS kèm nguyên văn
```

Báo "không thấy vấn đề gì" mà không kèm được thao tác đã làm thì gần như chắc chắn là chưa dùng — xem `/viper-dogfood §Dấu hiệu dogfood giả`.

## 5. Ranh giới

- Chỉ thao tác trên **localhost của dự án này** hoặc **URL production của chính nó**. Không đụng trang nào khác.
- Không sửa file dự án. Sáu vai `viper-user-*` đã bị chặn `Write`/`Edit` bằng frontmatter — phát hiện thì **báo**, việc sửa là của phiên chính.
- `browser_run_code_unsafe` chạy code tuỳ ý trong ngữ cảnh trang: dùng cho mô phỏng mạng và nhịp bấm, **không** dùng để đi tắt qua UI rồi kết luận "luồng chạy được". Đi tắt là hết dogfood.

## 6. Hỏng thì xem đây

| Triệu chứng | Nguyên nhân thường gặp |
|---|---|
| Server MCP không lên | `npx` trong PATH là gói standalone đời cũ, không hiểu `-y`. Template dùng `npm exec` chính vì vậy — `npm` chỉ có một bản nên không nhập nhằng |
| Lần đầu chạy rất lâu | Đang tải Chromium. Chạy trước `npx playwright install chromium` cho xong một lần |
| Trang trắng | App chưa chạy. `make dev` trước, và lấy đúng cổng (Next.js 3000 · FastAPI 8000 · Spring 8080) |
| Không thấy tool `browser_*` | Chưa duyệt server MCP cho dự án này. Duyệt một lần khi Claude Code hỏi |
