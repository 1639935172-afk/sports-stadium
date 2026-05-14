class StadiumComment {
  const StadiumComment({
    required this.id,
    required this.stadium,
    required this.userNickname,
    required this.content,
    required this.auditStatus,
    required this.createdAt,
  });

  final int id;
  final int stadium;
  final String userNickname;
  final String content;
  final String auditStatus;
  final String createdAt;

  factory StadiumComment.fromJson(Map<String, dynamic> json) {
    return StadiumComment(
      id: json['id'] as int,
      stadium: json['stadium'] as int? ?? 0,
      userNickname: json['user_nickname'] as String? ?? '',
      content: json['content'] as String? ?? '',
      auditStatus: json['audit_status'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}

class CommentCreateResult {
  const CommentCreateResult({
    required this.id,
    required this.stadium,
    required this.content,
    required this.auditStatus,
    required this.createdAt,
  });

  final int id;
  final int stadium;
  final String content;
  final String auditStatus;
  final String createdAt;

  factory CommentCreateResult.fromJson(Map<String, dynamic> json) {
    return CommentCreateResult(
      id: json['id'] as int,
      stadium: json['stadium'] as int? ?? 0,
      content: json['content'] as String? ?? '',
      auditStatus: json['audit_status'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}
