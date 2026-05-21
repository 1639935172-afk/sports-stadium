import 'package:flutter/material.dart';

import '../api/comment_api.dart';
import '../models/comment.dart';
import '../widgets/app_feedback.dart';

class AdminCommentAuditScreen extends StatefulWidget {
  const AdminCommentAuditScreen({super.key, required this.api});

  final CommentApi api;

  @override
  State<AdminCommentAuditScreen> createState() =>
      _AdminCommentAuditScreenState();
}

class _AdminCommentAuditScreenState extends State<AdminCommentAuditScreen> {
  var comments = <StadiumComment>[];
  var isLoading = true;
  var handlingCommentId = 0;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    _loadComments();
  }

  Future<void> _loadComments() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final result = await widget.api.adminPending();
      if (!mounted) return;
      setState(() {
        comments = result;
        isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = '无法加载待审核评论，请确认 Django 服务已启动。';
      });
    }
  }

  Future<void> _handleComment(
    StadiumComment comment,
    _CommentAction action,
  ) async {
    final actionLabel = switch (action) {
      _CommentAction.approve => '通过',
      _CommentAction.reject => '驳回',
      _CommentAction.delete => '删除',
    };

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('$actionLabel评论'),
          content: Text('确认$actionLabel来自 ${comment.userPhoneNumber} 的评论？'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('取消'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: Text('确认$actionLabel'),
            ),
          ],
        );
      },
    );

    if (confirmed != true) return;

    setState(() {
      handlingCommentId = comment.id;
    });

    try {
      switch (action) {
        case _CommentAction.approve:
          await widget.api.approve(commentId: comment.id);
        case _CommentAction.reject:
          await widget.api.reject(commentId: comment.id);
        case _CommentAction.delete:
          await widget.api.delete(commentId: comment.id);
      }
      if (!mounted) return;
      AppFeedback.showMessage(context, '评论已$actionLabel。');
      await _loadComments();
    } catch (_) {
      if (!mounted) return;
      AppFeedback.showMessage(
        context,
        '$actionLabel评论失败，请稍后重试。',
        isError: true,
      );
    } finally {
      if (mounted) {
        setState(() {
          handlingCommentId = 0;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(centerTitle: true, title: const Text('评论审核')),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadComments,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            children: [
              if (isLoading)
                const AppPageLoading()
              else if (errorMessage != null)
                AppMessagePanel(
                  icon: Icons.cloud_off,
                  message: errorMessage!,
                  action: TextButton.icon(
                    onPressed: _loadComments,
                    icon: const Icon(Icons.refresh),
                    label: const Text('重试'),
                  ),
                )
              else if (comments.isEmpty)
                const AppMessagePanel(
                  icon: Icons.rate_review_outlined,
                  message: '当前没有待审核评论。',
                )
              else
                for (final comment in comments) ...[
                  _CommentCard(
                    comment: comment,
                    isHandling: handlingCommentId == comment.id,
                    onApprove: handlingCommentId == 0
                        ? () => _handleComment(comment, _CommentAction.approve)
                        : null,
                    onReject: handlingCommentId == 0
                        ? () => _handleComment(comment, _CommentAction.reject)
                        : null,
                    onDelete: handlingCommentId == 0
                        ? () => _handleComment(comment, _CommentAction.delete)
                        : null,
                  ),
                  const SizedBox(height: 12),
                ],
            ],
          ),
        ),
      ),
    );
  }
}

enum _CommentAction { approve, reject, delete }

class _CommentCard extends StatelessWidget {
  const _CommentCard({
    required this.comment,
    required this.isHandling,
    required this.onApprove,
    required this.onReject,
    required this.onDelete,
  });

  final StadiumComment comment;
  final bool isHandling;
  final VoidCallback? onApprove;
  final VoidCallback? onReject;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) {
    final nickname = comment.userNickname.isEmpty
        ? '未设置昵称'
        : comment.userNickname;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              comment.stadiumName,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 10),
            _InfoRow(
              label: '用户',
              value: '$nickname (${comment.userPhoneNumber})',
            ),
            _InfoRow(label: '状态', value: _statusLabel(comment.auditStatus)),
            if (comment.createdAt.isNotEmpty)
              _InfoRow(label: '时间', value: _formatDateTime(comment.createdAt)),
            const SizedBox(height: 8),
            Text(comment.content),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: onApprove,
                  icon: isHandling
                      ? const AppLoadingIcon()
                      : const Icon(Icons.check_circle_outline),
                  label: const Text('通过'),
                ),
                OutlinedButton.icon(
                  onPressed: onReject,
                  icon: const Icon(Icons.cancel_outlined),
                  label: const Text('驳回'),
                ),
                OutlinedButton.icon(
                  onPressed: onDelete,
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('删除'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 48, child: Text(label)),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

String _statusLabel(String status) {
  return switch (status) {
    'pending' => '待审核',
    'approved' => '已通过',
    'rejected' => '已驳回',
    _ => status,
  };
}

String _formatDateTime(String value) {
  final normalized = value.replaceFirst('T', ' ');
  if (normalized.length >= 16) return normalized.substring(0, 16);
  return normalized;
}
