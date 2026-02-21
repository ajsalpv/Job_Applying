import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static String _baseUrl = 'https://job-applying.onrender.com';

  static Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    String url = prefs.getString('api_url') ?? _baseUrl;
    if (url.endsWith('/')) {
      url = url.substring(0, url.length - 1);
    }
    return url;
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
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('api_url', url);
    debugPrint('⚙️ [API] Base URL updated: $url');
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
