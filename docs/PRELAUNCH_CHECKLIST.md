# 上线前诊断与测试清单

## 1. 自动化诊断命令

在已激活 `sports_stadium` 环境后执行：

```powershell
python manage.py check
python manage.py check --deploy
python manage.py test sports_stadium accounts stadiums reservations comments --keepdb
python manage.py migrate --plan
```

当前自动化测试基线：

```text
85 tests OK
```

## 2. 当前 deploy check 结果

`python manage.py check --deploy` 当前会提示以下生产安全配置项：

- `SECURE_HSTS_SECONDS` 未设置。
- `SECURE_SSL_REDIRECT` 未设置为 `True`。
- `SECRET_KEY` 强度不足或仍使用开发默认值。
- `SESSION_COOKIE_SECURE` 未设置为 `True`。
- `CSRF_COOKIE_SECURE` 未设置为 `True`。

这些是上线环境必须处理的配置项。开发环境可以保留宽松配置，但生产环境应使用独立 `.env` 和部署配置。

## 3. 环境配置检查

上线前确认：

- `.env` 不提交到 Git。
- `.env.example` 不包含真实数据库密码。
- `SECRET_KEY` 使用生产随机强密钥。
- `DEBUG=False`。
- `ALLOWED_HOSTS` 填写真实域名或服务器 IP。
- MySQL 数据库、用户、权限已创建。
- 静态文件部署策略已确定。
- HTTPS 或反向代理的 SSL 终止已配置。

生产 HTTPS 场景建议配置：

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

启用 HSTS 前必须确认全站长期只通过 HTTPS 访问。

## 4. 数据库检查

上线前执行：

```powershell
python manage.py migrate --plan
python manage.py migrate
```

确认：

- `comments.0001_initial` 已应用。
- 业务库和测试库分离。
- 测试库权限正常。
- 不在生产库执行 `seed_demo`，除非明确需要演示数据。

## 5. 演示数据检查

本地演示可执行：

```powershell
python manage.py seed_demo
```

演示账号：

| 角色 | 手机号 | 密码 |
| --- | --- | --- |
| 系统管理员 | 18800000001 | DemoPass123 |
| 场馆管理员 | 18800000002 | DemoPass123 |
| 普通用户 | 18800000003 | DemoPass123 |

生产环境不要保留这些账号，除非它们被改成正式测试账号并使用强密码。

## 6. 主流程人工测试

### 普通用户

- 注册普通用户。
- 使用弱密码注册应显示密码校验错误。
- 登录成功后可进入场馆列表。
- 只能看到审核通过、开放、未申请删除的场馆。
- 可对未占用时段提交预约。
- 同一时段已有待审核或已通过预约时，其他用户不能重复预约。
- 可查看自己的预约。
- 可取消自己的待审核或已通过预约。
- 不能查看或取消其他用户预约。
- 可提交评论，评论默认待审核。
- 可删除自己的评论。

### 场馆管理员

- 注册场馆管理员必须填写正确注册码。
- 可提交场馆信息。
- 场馆审核通过后可维护场地。
- 只能维护自己负责的场馆、场地、时段。
- 可新增、编辑、停用、删除场地。
- 可新增、编辑、删除时段。
- 重叠时段应被拒绝，相邻时段允许。
- 可查看自己场馆下的待审核预约。
- 可通过或拒绝自己场馆下的预约。
- 不能审核其他场馆的预约。

### 系统管理员

- 可审核待审核场馆。
- 可处理场馆删除申请。
- 可审核待审核评论。
- 可删除任意评论。
- 可搜索用户。
- 可修改用户昵称、角色、登录状态、注销状态。
- 不能在用户管理页修改自己的账号，避免误锁。

## 7. 权限回归检查

至少确认以下 URL 的权限：

- 未登录访问 `/reservations/mine/` 会跳转登录。
- 普通用户访问 `/stadiums/mine/` 返回 403。
- 场馆管理员访问 `/reservations/mine/` 返回 403。
- 普通用户访问 `/comments/audit/` 返回 403。
- 非系统管理员访问 `/accounts/system/users/` 返回 403。
- 非负责人审核预约返回 404。

## 8. UI 与错误反馈检查

- 所有表单页展示字段错误。
- 登录、注册、密码修改、找回密码展示非字段错误。
- 列表为空时显示空状态。
- 成功或失败操作通过 messages 显示反馈。
- 删除、注销、取消类操作使用明显的危险按钮。
- 页面中文无乱码。
- 手机宽度下导航不重叠。

## 9. 发布前 Git 检查

```powershell
git status
git diff --check
```

确认：

- 没有 `.env` 或真实密钥进入 Git。
- 新增迁移文件已提交。
- 新增模板、管理命令、文档已提交。
- 没有无关生成文件。

## 10. 推荐发布前最终命令

```powershell
python manage.py check
python manage.py check --deploy
python manage.py test sports_stadium accounts stadiums reservations comments --keepdb
python manage.py migrate --plan
```

如果以上命令符合预期，再执行正式迁移和部署。
