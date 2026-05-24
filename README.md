# 体育场馆预约系统

基于 Django 5、MySQL、Django Templates 和 Flutter 的体育场馆预约系统。当前版本覆盖首个可演示主流程：注册登录、场馆提交与审核、场地和时段维护、模拟支付、用户预约、预约审核、评论审核、用户管理。

## 快速启动

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

访问：`http://127.0.0.1:8000/`

真实 `.env` 中需要按本机 MySQL 配置填写数据库账号和密码。不要提交真实 `.env`。

## 演示数据

生成可重复演示数据：

```powershell
python manage.py seed_demo
```

演示账号：

| 角色 | 手机号 | 密码 |
| --- | --- | --- |
| 系统管理员 | 18800000001 | DemoPass123 |
| 场馆管理员 | 18800000002 | DemoPass123 |
| 普通用户 | 18800000003 | DemoPass123 |

完整演示脚本见：`docs/DEMO.md`

## 常用命令

```powershell
python manage.py check
python manage.py test accounts stadiums reservations comments --keepdb
python manage.py migrate
```

移动端常用命令：

```powershell
cd mobile_app
flutter analyze
flutter run
```

Android 模拟器访问本机 Django 时，`mobile_app/lib/api/api_client.dart` 的 API 地址通常应使用：

```dart
baseUrl: 'http://10.0.2.2:8000/api'
```

如果使用真机调试，需要改成电脑当前局域网 IPv4，并确认防火墙允许访问 8000 端口。

## 主要角色

- 普通用户：浏览场馆、预约时段、模拟支付、查看/取消预约、发表评论、删除自己的评论。
- 场馆管理员：提交和维护自己的场馆、场地、时段，审核自己场馆下的预约。
- 系统管理员：审核场馆、审核评论、管理用户账号。

## 当前预约与支付流程

当前预约流程为“先支付，再审核”：

1. 普通用户在场馆详情中点击预约。
2. 系统生成待支付预约：`awaiting_payment`。
3. 系统同时生成支付单：`Payment(unpaid)`。
4. 用户在“我的预约”中点击“去支付”。
5. 支付成功后，预约进入 `pending`，等待场馆管理员审核。
6. 场馆管理员通过后预约变为 `approved`，拒绝后变为 `rejected`。
7. 支付失败会让预约进入 `payment_failed`，不进入管理员审核池。

过期待审核预约不会显示在场馆管理员的预约审核列表中；普通用户“我的预约”仍保留历史预约记录。

## 移动端体验

- 场馆详情页中，每个场地默认只展示前 3 条可预约时段。
- 可预约时段超过 3 条时，App 显示“查看全部”按钮。
- “查看全部”页面展示该场地全部可预约时段，并支持按日期筛选。
- App 的场馆管理员预约审核列表走 `/api/reservations/admin/pending/`，与 Web 共用过期过滤规则。

## 文档

- `docs/PRD.md`：产品需求说明。
- `docs/TASKS.md`：任务拆解。
- docs/DEMO.md：首个可演示主流程。
- docs/PRELAUNCH_CHECKLIST.md：上线前诊断与测试清单。

