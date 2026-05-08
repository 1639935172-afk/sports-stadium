# 体育场馆预约系统

基于 Django 5、MySQL 和 Django Templates 的体育场馆预约系统。当前版本覆盖首个可演示主流程：注册登录、场馆提交与审核、场地和时段维护、用户预约、预约审核、评论审核、用户管理。

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

## 主要角色

- 普通用户：浏览场馆、预约时段、查看/取消预约、发表评论、删除自己的评论。
- 场馆管理员：提交和维护自己的场馆、场地、时段，审核自己场馆下的预约。
- 系统管理员：审核场馆、审核评论、管理用户账号。

## 文档

- `docs/PRD.md`：产品需求说明。
- `docs/TASKS.md`：任务拆解。
- docs/DEMO.md：首个可演示主流程。
- docs/PRELAUNCH_CHECKLIST.md：上线前诊断与测试清单。

