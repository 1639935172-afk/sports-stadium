import 'package:flutter/material.dart';

import '../api/comment_api.dart';
import '../api/reservation_api.dart';
import '../api/stadium_api.dart';
import '../api/system_user_api.dart';
import '../models/stadium.dart';
import '../state/auth_state.dart';
import '../widgets/app_feedback.dart';
import 'admin_comment_audit_screen.dart';
import 'admin_pending_reservations_screen.dart';
import 'admin_stadium_audit_screen.dart';
import 'my_comments_screen.dart';
import 'my_reservations_screen.dart';
import 'my_stadiums_screen.dart';
import 'profile_screen.dart';
import 'stadium_detail_screen.dart';
import 'system_user_list_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.auth});

  final AuthState auth;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late final StadiumApi stadiumApi;
  late final ReservationApi reservationApi;
  late final CommentApi commentApi;
  late final SystemUserApi systemUserApi;
  final searchController = TextEditingController();

  var stadiums = <Stadium>[];
  var isLoading = true;
  String? errorMessage;

  bool get _isOrdinaryUser => widget.auth.user?.role == 'ordinary';
  bool get _isStadiumAdmin => widget.auth.user?.role == 'stadium_admin';
  bool get _isSystemAdmin => widget.auth.user?.role == 'system_admin';

  @override
  void initState() {
    super.initState();
    stadiumApi = StadiumApi(widget.auth.client);
    reservationApi = ReservationApi(widget.auth.client);
    commentApi = CommentApi(widget.auth.client);
    systemUserApi = SystemUserApi(widget.auth.client);
    _loadStadiums();
  }

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  Future<void> _loadStadiums() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final result = await stadiumApi.list(query: searchController.text);
      if (!mounted) return;
      setState(() {
        stadiums = result;
        isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = '无法连接后端，请确认 Django 服务已启动。';
      });
    }
  }

  void _clearSearch() {
    if (searchController.text.isEmpty) return;
    searchController.clear();
    _loadStadiums();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('场馆列表'),
        actions: [
          if (_isStadiumAdmin)
            IconButton(
              tooltip: '我的场馆',
              onPressed: _openMyStadiums,
              icon: const Icon(Icons.storefront_outlined),
            ),
          if (_isStadiumAdmin)
            IconButton(
              tooltip: '预约审核',
              onPressed: _openAdminPendingReservations,
              icon: const Icon(Icons.fact_check_outlined),
            ),
          if (_isSystemAdmin)
            IconButton(
              tooltip: '场馆审核',
              onPressed: _openAdminStadiumAudit,
              icon: const Icon(Icons.approval_outlined),
            ),
          if (_isSystemAdmin)
            IconButton(
              tooltip: '评论审核',
              onPressed: _openAdminCommentAudit,
              icon: const Icon(Icons.rate_review_outlined),
            ),
          if (_isSystemAdmin)
            IconButton(
              tooltip: '用户管理',
              onPressed: _openSystemUsers,
              icon: const Icon(Icons.manage_accounts_outlined),
            ),
          if (_isOrdinaryUser)
            IconButton(
              tooltip: '我的预约',
              onPressed: _openMyReservations,
              icon: const Icon(Icons.event_note_outlined),
            ),
          if (_isOrdinaryUser)
            IconButton(
              tooltip: '我的评论',
              onPressed: _openMyComments,
              icon: const Icon(Icons.chat_bubble_outline),
            ),
          IconButton(
            tooltip: '个人资料',
            onPressed: _openProfile,
            icon: const Icon(Icons.account_circle_outlined),
          ),
          IconButton(
            tooltip: '退出登录',
            onPressed: widget.auth.logout,
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: searchController,
                    textInputAction: TextInputAction.search,
                    decoration: InputDecoration(
                      labelText: '搜索场馆',
                      hintText: '输入名称或地址',
                      prefixIcon: const Icon(Icons.search),
                      suffixIcon: searchController.text.isEmpty
                          ? null
                          : IconButton(
                              tooltip: '清空',
                              onPressed: _clearSearch,
                              icon: const Icon(Icons.clear),
                            ),
                    ),
                    onChanged: (_) => setState(() {}),
                    onSubmitted: (_) => _loadStadiums(),
                  ),
                ),
                const SizedBox(width: 12),
                FilledButton.icon(
                  onPressed: isLoading ? null : _loadStadiums,
                  icon: const Icon(Icons.search),
                  label: const Text('搜索'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (isLoading)
              const AppPageLoading(topPadding: 80)
            else if (errorMessage != null)
              AppMessagePanel(
                icon: Icons.cloud_off,
                message: errorMessage!,
                action: TextButton.icon(
                  onPressed: _loadStadiums,
                  icon: const Icon(Icons.refresh),
                  label: const Text('重试'),
                ),
              )
            else if (stadiums.isEmpty)
              const AppMessagePanel(
                icon: Icons.search_off,
                message: '暂无符合条件的场馆。',
              )
            else
              for (final stadium in stadiums) ...[
                _StadiumCard(
                  stadium: stadium,
                  onTap: () => _openDetail(stadium),
                ),
                const SizedBox(height: 12),
              ],
          ],
        ),
      ),
    );
  }

  void _openDetail(Stadium stadium) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => StadiumDetailScreen(
          stadiumId: stadium.id,
          initialName: stadium.name,
          api: stadiumApi,
          reservationApi: reservationApi,
          commentApi: commentApi,
          canReserve: _isOrdinaryUser,
          canSubmitComment: _isOrdinaryUser,
        ),
      ),
    );
  }

  void _openMyReservations() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => MyReservationsScreen(api: reservationApi),
      ),
    );
  }

  void _openProfile() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(builder: (_) => ProfileScreen(auth: widget.auth)),
    );
  }

  void _openMyComments() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => MyCommentsScreen(api: commentApi),
      ),
    );
  }

  void _openSystemUsers() {
    final user = widget.auth.user;
    if (user == null) return;
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) =>
            SystemUserListScreen(api: systemUserApi, currentUserId: user.id),
      ),
    );
  }

  void _openAdminPendingReservations() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => AdminPendingReservationsScreen(api: reservationApi),
      ),
    );
  }

  void _openAdminCommentAudit() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => AdminCommentAuditScreen(api: commentApi),
      ),
    );
  }

  void _openAdminStadiumAudit() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => AdminStadiumAuditScreen(api: stadiumApi),
      ),
    );
  }

  void _openMyStadiums() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => MyStadiumsScreen(api: stadiumApi),
      ),
    );
  }
}

class _StadiumCard extends StatelessWidget {
  const _StadiumCard({required this.stadium, required this.onTap});

  final Stadium stadium;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      stadium.name,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  const Icon(Icons.chevron_right),
                ],
              ),
              const SizedBox(height: 10),
              _IconText(icon: Icons.place_outlined, text: stadium.address),
              _IconText(icon: Icons.phone_outlined, text: stadium.phoneNumber),
              if (stadium.information.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  stadium.information,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _IconText extends StatelessWidget {
  const _IconText({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18),
          const SizedBox(width: 8),
          Expanded(child: Text(text.isEmpty ? '未填写' : text)),
        ],
      ),
    );
  }
}
