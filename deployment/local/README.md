# deployment/local/ — chạy sản phẩm trên máy

> Quy ước đầy đủ: [`../README.md`](../README.md). Thư mục này **rỗng cho tới pha I** —
> pha V không dựng hạ tầng.

Pha I viết vào đây mọi thứ để `make dev` chạy được, thay vì rải ra gốc repo:

```
deployment/local/
├── docker-compose.yml   # DB local — xem .claude/skills/stack-<tên>/SKILL.md §2
├── .env                 # copy từ ../.env.example rồi điền — KHÔNG commit
├── init.sql / seed.*    # dữ liệu mẫu (nguồn: context/PRD.md §7)
└── …                    # chỉ thêm khi stack thật sự cần
```

Bắt đầu:

```bash
cp ../.env.example .env      # rồi điền giá trị local
make dev                     # từ gốc repo — thân lệnh trỏ vào compose ở đây
```

Ba thứ hay quên:

- **`make dev` phải tự lo DB.** Người dùng lệnh không cần biết compose nằm đâu — thân
  `make dev` gọi `docker compose -f deployment/local/docker-compose.yml up -d db` rồi mới
  chạy app. Bắt người ta chạy tay hai lệnh là hỏng hợp đồng lệnh.
- **Dữ liệu mẫu là điều kiện của dogfood**, không phải thứ "làm sau": `/viper-dogfood` đi
  hết luồng lõi trên dữ liệu thật trông ra sao, không phải trên bảng trống.
- **Đa target**: một compose cho cả hệ, không phải mỗi target một cái
  ([`srcroot/README.md`](../../srcroot/README.md)).
