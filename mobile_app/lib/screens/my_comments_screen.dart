import 'package:flutter/material.dart';
import 'package:dio/dio.dart';

import '../api/comment_api.dart';
import '../models/comment.dart';
import '../widgets/app_feedback.dart';

class MyCommentsScreen extends StatefulWidget {
  const MyCommentsScreen({super.key, required this.api});

  final CommentApi api;

  @override
  State<MyCommentsScreen> createState() => _MyCommentsScreenState();
}

class _MyCommentsScreenState extends State<MyCommentsScreen> {
  var comments = <StadiumComment>[];
  var isLoading = true;
  var deletingCommentId = 0;
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
      final result = await widget.api.mine();
      if (!mounted) return;
      setState(() {
        comments = result;
        isLoading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = _readLoadError(error);
      });
    }
  }

  Future<void> _confirmDelete(StadiumComment comment) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('删除评论'),
          content: Text('确认删除你在“${comment.stadiumName}”下的这条评论？'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('取消'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('确认删除'),
            ),
          ],
        );
      },
    );

    if (confirmed == true) {
      await _deleteComment(comment.id);
    }
  }

  Future<void> _deleteComment(int commentId) async {
    setState(() {
      deletingCommentId = commentId;
    });

    try {
      await widget.api.deleteMine(commentId: commentId);
      if (!mounted) return;
      AppFeedback.showMessage(context, '评论已删除。');
      await _loadComments();
    } catch (_) {
      if (!mounted) return;
      AppFeedback.showMessage(context, '删除评论失败，请稍后重试。', isError: true);
    } finally {
      if (mounted) {
        setState(() {
          deletingCommentId = 0;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(centerTitle: true, title: const Text('我的评论')),
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
                  message: '暂无评论记录。',
                )
              else
                for (final comment in comments) ...[
                  _CommentCard(
                    comment: comment,
                    isDeleting: deletingCommentId == comment.id,
                    canDelete: deletingCommentId == 0,
                    onDelete: () => _confirmDelete(comment),
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

class _CommentCard extends StatelessWidget {
  const _CommentCard({
    required this.comment,
    required this.isDeleting,
    required this.canDelete,
    required this.onDelete,
  });

  final StadiumComment comment;
  final bool isDeleting;
  final bool canDelete;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    comment.stadiumName,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                _StatusBadge(status: comment.auditStatus),
              ],
            ),
            if (comment.createdAt.isNotEmpty) ...[
              const SizedBox(height: 10),
              _IconText(
                icon: Icons.schedule,
                text: _formatDateTime(comment.createdAt),
              ),
            ],
            const SizedBox(height: 10),
            Text(comment.content),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: OutlinedButton.icon(
                onPressed: canDelete ? onDelete : null,
                icon: isDeleting
                    ? const AppLoadingIcon()
                    : const Icon(Icons.delete_outline),
                label: Text(isDeleting ? '删除中' : '删除评论'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final (label, color) = switch (status) {
      'pending' => ('待审核', colorScheme.primary),
      'approved' => ('已通过', Colors.green),
      'rejected' => ('已驳回', colorScheme.error),
      _ => (status, colorScheme.outline),
    };

    return Chip(
      label: Text(label),
      visualDensity: VisualDensity.compact,
      side: BorderSide(color: color),
      labelStyle: TextStyle(color: color),
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

String _readLoadError(Object error) {
  if (error is DioException && error.response?.statusCode == 401) {
    return '登录状态已失效，请退出后重新登录。';
  }
  return '无法加载我的评论，请确认 Django 服务已启动。';
}

String _formatDateTime(String value) {
  final normalized = value.replaceFirst('T', ' ');
  if (normalized.length >= 16) return normalized.substring(0, 16);
  return normalized;
}
