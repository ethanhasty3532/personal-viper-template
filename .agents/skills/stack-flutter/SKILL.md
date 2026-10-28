---
name: stack-flutter
description: >
  Stack Flutter/Dart cho app VIPER, dùng flutter_bloc với Cubit mặc định và Bloc
  khi cần điều phối sự kiện. Nạp khi TECHSTACK chốt stack-flutter hoặc pha V
  chọn Flutter; gồm kiến trúc theo tính năng, sáu lệnh, test và phát hành mobile/web.
---

# Stack — Flutter với BLoC/Cubit

## 1. Khi nào chọn / không chọn

Chọn khi sản phẩm cần app Flutter Android/iOS, hoặc Flutter Web theo yêu cầu.
Không mặc định dùng Flutter cho trang nội dung cần SEO. Skill này là client,
không cung cấp API server hay DB server. Chốt backend có sẵn, dịch vụ managed
hoặc target backend riêng ở pha V; không tự thêm target ngoài ARCHITECTURE.

Mặc định dùng **Cubit** với các phương thức có tên nghiệp vụ. Dùng **Bloc** khi
cần sự kiện tường minh và chiến lược xử lý đồng thời; ghi lý do trong DECISIONS.
Bloc không tự bảo đảm xử lý tuần tự: chọn transformer phù hợp khi cần.
Intake TECHSTACK thắng các mặc định của skill này.

Đường phỏng vấn: một app ở gốc repo, backend managed/có sẵn nếu phù hợp; nếu cần
nhiều target độc lập thì chọn đường intake ngay ở pha V. Đường intake: app ở
`srcroot/mobile-experiences/<tên>/`, hoặc `web-experiences/<tên>/` nếu là target web
đã khai. Chỉ dựng target thuộc vòng hiện tại.

## 2. Scaffold

Kiểm `flutter --version`, `flutter doctor -v`, `flutter devices`. Chốt nền tảng,
application ID/bundle ID và kênh phát hành trong TECHSTACK trước khi scaffold.
Chọn Flutter stable tương thích, ghi phiên bản thật ở TECHSTACK §4; commit
`pubspec.lock` cho app. Không cài nâng SDK toàn máy chỉ để khớp ví dụ.

Trong thư mục target đã chọn (giữ Makefile và .gitignore của template):
Nếu scaffold ở gốc đang có README/cấu hình, tạo dự án trong thư mục tạm rồi ghép
file Flutter vào, tránh để CLI ghi đè tài liệu template và các quy tắc ignore.

```bash
flutter create --project-name my_app --org com.example --platforms=android,ios,web .
flutter pub add flutter_bloc equatable
flutter pub add dev:bloc_test dev:mocktail
flutter pub add 'dev:integration_test:{sdk: flutter}'
```

`my_app`, `com.example` và danh sách platform là ví dụ, phải thay bằng giá trị
đã chốt; không tạo platform không dùng. Chỉ thêm client REST/GraphQL, routing,
secure storage, DI hay codegen khi kiến trúc thật cần; không ép GraphQL.

Cấu hình local ở `deployment/local/`, danh sách biến ở `deployment/.env.example`.
Nếu dùng `--dart-define-from-file`, đặt JSON local ở đó và ignore file này.
Chỉ đưa cấu hình công khai như API base URL vào binary. API key bí mật, service
account và quyền quản trị ở backend; dart-define hay obfuscation không giấu secret.
Android emulator cần địa chỉ host phù hợp (thường `10.0.2.2`); điện thoại thật
cần địa chỉ truy cập được, không mặc định dùng localhost của máy phát triển.

## 3. Cấu trúc và quản lý state

```text
lib/
  app/                       # bootstrap, router, theme, cung cấp dependency
  core/                      # cấu hình, lỗi và tiện ích dùng chung
  features/<feature>/
    data/                    # datasource, DTO, repository implementation
    domain/                  # entity, repository contract; usecase khi cần
    presentation/
      cubit/                 # feature_cubit.dart, feature_state.dart
      pages/
      widgets/
test/                        # Cubit, repository, widget
integration_test/            # luồng lõi trên platform mục tiêu
```

Luồng: Page → Cubit → repository (qua usecase nếu cần) → datasource.
State bất biến, thể hiện initial/loading/success/empty/failure theo màn hình.
Không thêm tầng usecase chỉ để chuyển tiếp một lời gọi.

- Widget không gọi API hay chứa nghiệp vụ; Cubit không giữ BuildContext.
- `BlocProvider(create: ...)` tạo Cubit theo vòng đời màn và tự close; instance
  truyền qua `BlocProvider.value` do bên tạo chịu trách nhiệm close.
- `BlocBuilder` dựng UI; `BlocListener` xử lý điều hướng, snackbar và dialog.
- Không gọi tải dữ liệu từ `build`; tránh tạo Cubit mới mỗi lần rebuild.
- Huỷ subscription khi close; chống emit sau close và kết quả request cũ ghi đè
  kết quả mới. Luồng ghi cần chống gửi lặp ở client và idempotency ở server.
- State toàn app chỉ dành cho dữ liệu thực sự dùng chung như phiên đăng nhập;
  Cubit của màn hình không phụ thuộc trực tiếp vào Cubit của màn hình khác.

## 4. Sáu lệnh Makefile

Hiện thực sáu lệnh ở pha I theo nền tảng đã chốt. Ví dụ dưới đây cho target web
có thư mục `lib/`, chạy từ thư mục app; không thay Makefile template trước pha I:

```makefile
STACK_SKILL = stack-flutter
DEVICE ?= chrome

.PHONY: dev check test migrate deploy doctor
dev:
	flutter run -d $(DEVICE)
check:
	dart format --output=none --set-exit-if-changed lib test integration_test
	flutter analyze
	flutter build web
test:
	flutter test
migrate:
	@echo "Client không có DB/schema riêng; migration do backend quản lý."
deploy:
	./deployment/publish.sh
doctor:
	flutter doctor -v
	flutter devices
```

Chỉ liệt kê thư mục test thực sự có. Với mobile, thay build web bằng
`flutter build apk --debug` hoặc `flutter build ios --simulator --no-codesign`
trên runner phù hợp; không bỏ build khỏi check. Chạy integration test riêng:
`flutter test integration_test -d <device-id>` trên emulator/thiết bị hỗ trợ.
CI phải chọn device thật có sẵn; không báo test đạt chỉ vì script được tạo.

`migrate` chỉ được giải thích không áp dụng khi không có schema client; có DB
local thì phải chạy/thử migration và giữ dữ liệu cũ. Backend migration chạy ở
target backend. `deployment/publish.sh` là script cần hiện thực theo kênh đã chốt,
phải báo lỗi khi thiếu cấu hình; build artifact đơn thuần chưa phải publish.
Đường intake: Makefile gốc điều phối xuống target, deploy luôn qua root
`make deploy` để guard_bc còn hiệu lực. Đường dẫn deployment tính từ gốc repo.

## 5. Preset production-ready

| Mục | Cách áp dụng |
|---|---|
| Auth | Provider đã chốt; token ở secure storage phù hợp platform, không lưu password |
| Phân quyền | Backend kiểm quyền từng request; ẩn nút không thay phân quyền |
| Network | Timeout, ánh xạ lỗi có thông báo; chỉ retry khi an toàn; không log token/PII |
| State | Có trạng thái rỗng/lỗi/tải, thử lại; chống bấm gửi lặp và request đua nhau |
| Thiết bị | Quyền tối thiểu; thử bị từ chối quyền, background/resume, bàn phím và nút back |
| Theo dõi | Error tracking và analytics theo PRD, tách môi trường và lọc dữ liệu nhạy cảm |
| CI | Pin SDK, pub get, format, analyze, test, build và integration test phù hợp |
| Backend | Health, backup, rate limit và migration thuộc backend/managed service |

Rà đủ bốn nhóm shared-production-ready. Mục server không áp dụng cho client
phải ghi lý do và target chịu trách nhiệm; không tick xanh thay cho bằng chứng.

## 6. Phát hành và dogfood

Chốt kênh ở pha V: web hosting, Android internal testing/Play Store,
iOS TestFlight/App Store. Key ký, provisioning và credential CI nằm ngoài Git;
không tự đăng ký tài khoản trả phí hay công bố nếu chưa được phép.
Android dùng `flutter build appbundle`; iOS dùng `flutter build ipa` trên macOS
với signing hợp lệ. Hai lệnh chỉ build; upload/release cần quy trình riêng.

Ghi artifact/version, kênh phân phối, smoke test và rollback ở DEPLOY.md.
App store có độ trễ: giữ API tương thích với app cũ; rollback có thể là dừng
rollout và phát hành bản sửa mới, không hứa hạ version đã cài trên mọi máy.
P1/P2 vẫn cần bằng chứng phân phối, smoke và diễn tập phục hồi thực tế.

Dogfood vẫn đủ meta + sáu vai, hai đợt tối đa ba vai, giữ quy tắc dữ liệu chung.
Nếu hỗ trợ web, chạy `flutter run -d web-server --web-port=8080` rồi dùng
`viper-browse`/Playwright MCP; nếu Flutter canvas không cung cấp locator, dùng
ảnh chụp và thao tác tọa độ mà công cụ thực sự hỗ trợ, hoặc integration_test.
Không suy từ DOM rỗng rằng màn hình không có lỗi.

Web chỉ chứng minh luồng web. Push, camera, deep link, permission, secure storage,
back và lifecycle phải dùng emulator/thiết bị mục tiêu. Ghi platform, device,
persona, thao tác, kết quả và ảnh/log thật. Nếu thiếu công cụ native hoặc browser
riêng cho subagent, ghi blocker/phần chưa kiểm chứng; không báo dogfood native đạt.

## 7. Forbidden patterns

Không dùng secret trong app, gọi API từ widget, mutate state/list đã emit,
nuốt exception, log toàn bộ auth state, hoặc giả lập thành công thay dữ liệu thật.
Không dùng hydrated state để lưu token, không retry vô hạn luồng ghi, không dùng
web viewport nhỏ để kết luận app Android/iOS đã được kiểm thử.

## 8. Mẫu nối Cubit và UI

```dart
BlocProvider(
  create: (context) => ProductsCubit(
    context.read<ProductsRepository>(),
  )..load(),
  child: const ProductsPage(),
)
```

`ProductsRepository` được cung cấp ở composition root; các lớp ở trên là ví dụ
tên feature cần hiện thực. Dùng `bloc_test` kiểm chuỗi loading → success/failure,
thêm ca kết quả cũ về sau, close giữa request và gửi hai lần khi luồng có rủi ro.
Widget test kiểm trạng thái và retry; integration test đi hết AC lõi.

Nguồn chính thức: [Flutter testing](https://docs.flutter.dev/testing/overview),
[integration_test](https://docs.flutter.dev/testing/integration-tests),
[Flutter Bloc](https://bloclibrary.dev/flutter-bloc-concepts/),
[Bloc testing](https://bloclibrary.dev/testing/).
