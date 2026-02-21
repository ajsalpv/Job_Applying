import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String _baseUrl = 'https://job-applying-agent.onrender.com';

  static Future<String> getBaseUrl() async {
    // URL is now hardcoded for stability as requested
    return _baseUrl;
  }

  static Future<Map<String, dynamic>> getStats() async {
    final base = await getBaseUrl();
    final url = '$base/api/applications/stats';
    debugPrint('📡 [API] GET: $url');
    try {
      final response = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 15));
      debugPrint('📥 [API] Response: ${response.statusCode}');
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      throw Exception('Server error: ${response.statusCode}');
    } catch (e) {
      debugPrint('❌ [API] Error: $e');
      rethrow;
    }
  }

  static Future<void> setBaseUrl(String url) async {
    // No longer supported as URL is hardcoded
    debugPrint('⚙️ [API] Base URL change requested but ignored (Fixed to $_baseUrl)');
  }

  static Future<List<dynamic>> getAllApplications() async {
    final base = await getBaseUrl();
    final url = '$base/api/applications';
    debugPrint('📡 [API] GET: $url');
    try {
      final response = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 15));
      debugPrint('📥 [API] Response: ${response.statusCode}');
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['applications'] ?? [];
      }
      throw Exception('Server error: ${response.statusCode}');
    } catch (e) {
      debugPrint('❌ [API] Error: $e');
      rethrow;
    }
  }

  static Future<Map<String, dynamic>> getJobsByPlatform(String platform) async {
    final base = await getBaseUrl();
    final url = '$base/api/jobs/by-platform/$platform';
    debugPrint('📡 [API] GET: $url');
    try {
      final response = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 15));
      debugPrint('📥 [API] Response: ${response.statusCode}');
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      throw Exception('Server error: ${response.statusCode}');
    } catch (e) {
      debugPrint('❌ [API] Error: $e');
      rethrow;
    }
  }

  static Future<Map<String, dynamic>> getSupervisorStatus() async {
    final base = await getBaseUrl();
    final url = '$base/api/supervisor/status';
    debugPrint('📡 [API] GET: $url');
    try {
      final response = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 15));
      debugPrint('📥 [API] Response: ${response.statusCode}');
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      throw Exception('Server error: ${response.statusCode}');
    } catch (e) {
      debugPrint('❌ [API] Error: $e');
      rethrow;
    }
  }

  static Future<void> reEnablePlatform(String platform) async {
    final base = await getBaseUrl();
    final url = '$base/api/supervisor/re-enable/$platform';
    debugPrint('📡 [API] POST: $url');
    try {
      final response = await http.post(Uri.parse(url)).timeout(const Duration(seconds: 10));
      debugPrint('📥 [API] Response: ${response.statusCode}');
      if (response.statusCode != 200) {
        throw Exception('Server error: ${response.statusCode}');
      }
    } catch (e) {
      debugPrint('❌ [API] Error: $e');
      rethrow;
    }
  }

  static Future<void> triggerScan() async {
    final base = await getBaseUrl();
    final response = await http.post(
      Uri.parse('$base/api/jobs/scan'),
    ).timeout(const Duration(seconds: 10));
    if (response.statusCode != 200) {
      throw Exception('Failed to trigger scan: ${response.statusCode}');
    }
  }

  static Future<void> updateStatus(String company, String role, String status, {String? notes, String? appliedAt}) async {
    final base = await getBaseUrl();
    final url = '$base/api/applications/status';
    final response = await http.post(
      Uri.parse(url),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'company': company,
        'role': role,
        'status': status,
        'notes': notes ?? '',
        'applied_at': appliedAt,
      }),
    ).timeout(const Duration(seconds: 10));
    if (response.statusCode != 200) {
      throw Exception('Failed to update status: ${response.statusCode}');
    }
  }

  static Future<Map<String, dynamic>> getAppSettings() async {
    final base = await getBaseUrl();
    final url = '$base/api/settings';
    final response = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 10));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to get settings');
  }

  static Future<void> updateAppSettings(Map<String, dynamic> settings) async {
    final base = await getBaseUrl();
    final url = '$base/api/settings';
    final response = await http.post(
      Uri.parse(url),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(settings),
    ).timeout(const Duration(seconds: 10));
    if (response.statusCode != 200) {
      throw Exception('Failed to update settings');
    }
  }

  static Future<Map<String, dynamic>> getHealth() async {
    final base = await getBaseUrl();
    final response = await http.get(
      Uri.parse('$base/api/health'),
    ).timeout(const Duration(seconds: 10));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Server unreachable');
  }
}
