import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static String _baseUrl = 'https://job-applying.onrender.com';

  static Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString('api_url') ?? _baseUrl;
    return _baseUrl;
  }

  static Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('api_url', url);
    _baseUrl = url;
  }

  static Future<Map<String, dynamic>> getStats() async {
    final base = await getBaseUrl();
    final response = await http.get(
      Uri.parse('$base/api/applications/stats'),
    ).timeout(const Duration(seconds: 15));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to load stats: ${response.statusCode}');
  }

  static Future<List<dynamic>> getAllApplications() async {
    final base = await getBaseUrl();
    final response = await http.get(
      Uri.parse('$base/api/applications'),
    ).timeout(const Duration(seconds: 15));
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['applications'] ?? [];
    }
    throw Exception('Failed to load applications: ${response.statusCode}');
  }

  static Future<Map<String, dynamic>> getJobsByPlatform(String platform) async {
    final base = await getBaseUrl();
    final response = await http.get(
      Uri.parse('$base/api/jobs/by-platform/$platform'),
    ).timeout(const Duration(seconds: 15));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to load $platform jobs: ${response.statusCode}');
  }

  static Future<Map<String, dynamic>> getSupervisorStatus() async {
    final base = await getBaseUrl();
    final response = await http.get(
      Uri.parse('$base/api/supervisor/status'),
    ).timeout(const Duration(seconds: 15));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to load supervisor status: ${response.statusCode}');
  }

  static Future<void> reEnablePlatform(String platform) async {
    final base = await getBaseUrl();
    final response = await http.post(
      Uri.parse('$base/api/supervisor/re-enable/$platform'),
    ).timeout(const Duration(seconds: 10));
    if (response.statusCode != 200) {
      throw Exception('Failed to re-enable $platform: ${response.statusCode}');
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
