class StadiumComment {
  const StadiumComment({
    required this.id,
    required this.userId,
    required this.stadium,
    required this.stadiumName,
    required this.userNickname,
    required this.userPhoneNumber,
    required this.content,
    required this.auditStatus,
    required this.createdAt,
  });

  final int id;
  final int userId;
  final int stadium;
  final String stadiumName;
  final String userNickname;
  final String userPhoneNumber;
  final String content;
  final String auditStatus;
  final String createdAt;

  factory StadiumComment.fromJson(Map<String, dynamic> json) {
    return StadiumComment(
      id: json['id'] as int,
      userId: json['user'] as int? ?? 0,
      stadium: json['stadium'] as int? ?? 0,
      stadiumName: json['stadium_name'] as String? ?? '',
      userNickname: json['user_nickname'] as String? ?? '',
      userPhoneNumber: json['user_phone_number'] as String? ?? '',
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
