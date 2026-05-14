class AppUser {
  const AppUser({
    required this.id,
    required this.phoneNumber,
    required this.nickname,
    required this.role,
    required this.isActive,
    required this.isCancelled,
  });

  final int id;
  final String phoneNumber;
  final String nickname;
  final String role;
  final bool isActive;
  final bool isCancelled;

  factory AppUser.fromJson(Map<String, dynamic> json) {
    return AppUser(
      id: json['id'] as int,
      phoneNumber: json['phone_number'] as String? ?? '',
      nickname: json['nickname'] as String? ?? '',
      role: json['role'] as String? ?? '',
      isActive: json['is_active'] as bool? ?? true,
      isCancelled: json['is_cancelled'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'phone_number': phoneNumber,
      'nickname': nickname,
      'role': role,
      'is_active': isActive,
      'is_cancelled': isCancelled,
    };
  }
}
