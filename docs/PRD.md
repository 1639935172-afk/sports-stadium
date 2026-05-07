# 体育场馆预约系统 PRD

## Problem Statement

传统体育场馆预约依赖现场排队、人工登记或电话沟通，用户难以及时了解场馆、场地和时段的可预约状态，预约成功率和体验不稳定。场馆管理方也难以集中维护场馆信息、场地资源、开放时段、预约申请和用户评价，容易出现信息不透明、资源闲置、人工审核低效和数据不一致等问题。

本项目需要建设一个体育场馆预约系统，让用户可以在线查看场馆与场地、选择时段并提交预约，让场馆管理员可以维护场馆资源并审核预约，让系统管理员可以维护平台秩序和审核内容。

## Solution

建设一个以 Web 端为优先实现目标、后续可扩展移动端/App 的体育场馆预约系统。系统采用三类用户角色：

- 普通用户：预约场地、管理个人账户、查看场馆/场地/时段、管理自己的预约和评论。
- 场馆管理员：发布和维护自己负责的场馆、场地、时段，审核用户预约申请。
- 系统管理员：管理用户账户，审核场馆信息和评论，维护平台内容合规性。

系统功能按业务域拆分为账户与权限、场馆管理、场地管理、时段管理、预约管理、评论管理、后台审核与管理。首期以 Web 端完整闭环为目标，移动端/App 可在核心业务稳定后复用后端接口扩展。

## User Stories

1. As a visitor, I want to register with my phone number and password, so that I can use the booking system.
2. As a visitor, I want the system to reject an already-registered phone number, so that duplicate accounts are avoided.
3. As a visitor, I want to confirm my password during registration, so that accidental password entry errors are caught.
4. As a visitor, I want to verify registration with an SMS-style verification code, so that account ownership is confirmed.
5. As a registered user, I want to log in with phone number and password, so that I can access protected features.
6. As a registered user, I want to log in with phone number and verification code, so that I can log in without remembering my password.
7. As a registered user, I want to reset a forgotten password with my phone number and verification code, so that I can recover access to my account.
8. As a registered user, I want to view my account information, so that I can confirm my profile is correct.
9. As a registered user, I want to update my nickname or contact information, so that my profile stays current.
10. As a registered user, I want to change my password after verifying my identity, so that my account remains secure.
11. As a registered user, I want to cancel my account after verification, so that I can stop using the system.
12. As a system administrator, I want to search user accounts, so that I can manage platform users.
13. As a system administrator, I want to disable or cancel non-admin user accounts, so that problematic accounts can be handled.
14. As a user, I want to browse published stadiums, so that I can find suitable sports venues.
15. As a user, I want to search stadiums by name, so that I can quickly locate a specific stadium.
16. As a user, I want to view stadium details, so that I can understand address, contact information, introduction and available resources.
17. As a stadium administrator, I want to submit a new stadium for review, so that my venue can appear in the platform after approval.
18. As a stadium administrator, I want to edit my stadium information and resubmit it for review, so that outdated information can be corrected safely.
19. As a stadium administrator, I want to request stadium deletion, so that closed or invalid venues can be removed.
20. As a system administrator, I want to review new stadium submissions, so that only valid stadiums are published.
21. As a system administrator, I want to approve or reject stadium modification submissions, so that published information remains reliable.
22. As a stadium administrator, I want to add fields under an approved stadium, so that users can book specific sports spaces.
23. As a stadium administrator, I want to update field information such as type, code, status and price, so that users see accurate booking options.
24. As a stadium administrator, I want to delete fields I manage, so that unavailable fields are no longer bookable.
25. As a user, I want to view fields under a stadium, so that I can choose the correct sport type and location.
26. As a user, I want to see field prices, so that I can choose based on cost.
27. As a stadium administrator, I want to create open time periods for a field, so that users can book by time slot.
28. As a stadium administrator, I want the system to reject conflicting time periods, so that booking slots do not overlap.
29. As a stadium administrator, I want to modify a time period, so that opening arrangements can change.
30. As a stadium administrator, I want to delete a time period, so that unavailable slots stop accepting reservations.
31. As a user, I want to see available and unavailable slots for a chosen date, so that I can avoid already-booked periods.
32. As a user, I want booked slots to appear unavailable, so that I do not submit an impossible reservation.
33. As a user, I want to submit a reservation for a field, date and time period, so that I can use a sports venue.
34. As a user, I want to view my submitted reservations, so that I can track their status.
35. As a user, I want to cancel my own pending or approved reservation, so that I can give up a slot I no longer need.
36. As a stadium administrator, I want to view pending reservations for fields I manage, so that I can process booking requests.
37. As a stadium administrator, I want to approve a reservation, so that the selected field and period become occupied.
38. As a stadium administrator, I want to reject a reservation, so that invalid or unsuitable requests do not occupy resources.
39. As a stadium administrator, I want to view approved reservation user information, so that I can manage on-site usage.
40. As a user, I want to publish a comment under a stadium, so that I can share feedback.
41. As a user, I want my comment to enter pending review before publication, so that the platform can moderate content.
42. As a system administrator, I want to approve or reject comments, so that inappropriate comments are filtered.
43. As a user, I want to view approved comments, so that I can learn from other users' experiences.
44. As a user, I want to delete my own comment, so that I can remove content I no longer want to show.
45. As a system administrator, I want to delete any comment, so that harmful or invalid content can be removed after publication.
46. As a user, I want clear error messages for invalid input, so that I can correct mistakes quickly.
47. As a user, I want most operations to respond within about one second, so that the system feels usable.
48. As a developer, I want role permissions to be explicit, so that unauthorized operations are prevented consistently.
49. As a developer, I want booking state transitions to be centralized, so that reservation conflicts and invalid transitions are avoided.
50. As a developer, I want audit states to be modeled explicitly, so that review workflows are reliable and testable.

## Implementation Decisions

- Use three explicit user roles: ordinary user, stadium administrator and system administrator. This resolves the document conflict where early drafts let ordinary users act as venue publishers while later drafts introduce a dedicated stadium administrator.
- Prioritize a Web application as the first deliverable. Mobile/App support is treated as a later extension that can reuse backend domain logic and APIs.
- Use Python for backend development and MySQL for persistent storage, matching the project proposal.
- Prefer Django for the first implementation because it provides built-in authentication, ORM, admin tooling, forms, migrations and test support suitable for this management-heavy system.
- Build deep, testable domain modules around booking availability, audit workflows and role permission checks. These should hide implementation detail behind stable service-level interfaces.
- Suggested application modules:
  - Accounts and authorization: users, roles, login, registration, password reset, profile updates and account cancellation.
  - Stadiums: stadium submission, editing, deletion request, search, display and system-admin audit.
  - Fields: field creation, editing, deletion, pricing and status management under approved stadiums.
  - Periods: time-slot creation, editing, deletion and overlap validation.
  - Reservations: availability display, submission, approval, rejection, cancellation and reservation status tracking.
  - Comments: comment creation, review, display and deletion.
  - Admin/back-office: user management, stadium audit, comment audit and operational dashboards.
- Model audit states explicitly:
  - Stadium audit status: pending, approved, rejected.
  - Comment audit status: pending, approved, rejected.
  - Reservation status: pending, approved, rejected, cancelled.
- A stadium must be approved before fields can be published under it.
- A field must be open/active before users can submit reservations for it.
- A period must not overlap with existing periods for the same field.
- A reservation must not be approved if another approved reservation already occupies the same field and period.
- Deleting a field with existing approved reservations requires a later payment/refund policy. In the first implementation, this can be represented as a guarded operation or documented manual workflow unless online payment is added.
- Verification codes can be implemented as a development stub in the first version if real SMS integration is not available. The interface should leave room for replacing the stub with a real provider.
- The system should use server-side validation for all submitted data, even when client-side validation exists.
- Search should initially support stadium name search. More advanced filters such as location, sport type, price and rating can be added later.
- Browser support follows the requirement of desktop and mobile browsers. Exact compatibility with older browsers such as IE 11 can be treated as best effort unless mandated by acceptance testing.

## Testing Decisions

- Tests should verify external behavior and business rules rather than implementation details.
- Accounts tests should cover registration validation, duplicate phone rejection, login success/failure, password reset, profile update and account cancellation.
- Permission tests should cover role boundaries, including ordinary users being blocked from admin actions and stadium administrators being limited to their own stadiums/fields/reservations.
- Stadium tests should cover submission, approval, rejection, editing, deletion request and search visibility.
- Field tests should cover creation under approved stadiums, invalid creation under unapproved stadiums, updates, status changes and deletion rules.
- Period tests should cover non-overlapping creation, overlap rejection, updates and deletion.
- Reservation tests should cover availability display, submission, approval, rejection, cancellation and conflict prevention.
- Comment tests should cover pending review, approval visibility, rejection hiding, user deletion and administrator deletion.
- Integration tests should cover end-to-end flows:
  - user registers, logs in, views stadium, submits reservation, stadium administrator approves it;
  - stadium administrator submits stadium, system administrator approves it, ordinary user can view it;
  - ordinary user submits comment, system administrator approves it, comment becomes visible.
- Performance targets from the requirements should guide implementation, but first-phase automated tests should focus on correctness. Load/performance testing can be added after the main workflow is complete.

## Out of Scope

- Real online payment, refund and settlement workflows.
- Real SMS provider integration, unless credentials and provider details are supplied.
- Full native Android or Flutter App implementation in the first Web milestone.
- Social features from competitor products, such as AA booking, sharing, notes, sports communities or training reservations.
- Advanced recommendation, ranking, map-based nearby venue discovery or intelligent sorting.
- Complex financial reporting for stadium operators.
- Multi-tenant enterprise administration beyond the three defined user roles.

## Further Notes

- The project documents mention both Web and App. The first implementation should complete the Web management and reservation loop before expanding to App.
- The document set uses both `Field` and `Fields`; the implementation should choose one consistent domain name. `Field` is recommended for code and database model naming.
- The document set contains legacy wording such as “志愿活动” in a few places. These appear to be template remnants and should be interpreted as “体育场馆/场地预约” in this project.
- The project should treat “场馆管理员” as the owner/operator role for stadium and field resources.
- The first milestone should produce a usable vertical slice: login, approved stadium listing, field/period availability, reservation submission and reservation audit.
