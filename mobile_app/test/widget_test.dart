import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_app/main.dart';
void main() { testWidgets('shows login screen before authentication', (tester) async { await tester.pumpWidget(const SportsStadiumApp()); await tester.pumpAndSettle(); expect(find.text('体育场馆预约系统'), findsOneWidget); expect(find.text('普通用户移动端登录'), findsOneWidget); expect(find.text('登录'), findsOneWidget); expect(find.text('注册新账号'), findsOneWidget); }); }
