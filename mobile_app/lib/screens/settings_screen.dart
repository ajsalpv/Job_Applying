import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _urlController = TextEditingController();
  bool _connected = false;
  bool _testing = false;
  String? _serverInfo;

  @override
  void initState() {
    super.initState();
    _loadUrl();
  }

  Future<void> _loadUrl() async {
    final url = await ApiService.getBaseUrl();
    _urlController.text = url;
  }

  Future<void> _testConnection() async {
    setState(() { _testing = true; });
    try {
      await ApiService.setBaseUrl(_urlController.text.trim());
      final health = await ApiService.getHealth();
      setState(() {
        _connected = true;
        _testing = false;
        _serverInfo = 'Status: ${health['status']} | Loop: ${health['loop']}';
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('✅ Connected to server!'),
            backgroundColor: AppTheme.success,
          ),
        );
      }
    } catch (e) {
      setState(() {
        _connected = false;
        _testing = false;
        _serverInfo = 'Error: $e';
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Connection failed: $e'),
            backgroundColor: AppTheme.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Text('⚙️ ', style: TextStyle(fontSize: 22)),
            Text('Settings'),
          ],
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Server Config
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.surfaceLighter),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.cloud_rounded, color: AppTheme.primary),
                    SizedBox(width: 10),
                    Text(
                      'API Server',
                      style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                const Text(
                  'Enter your Render backend URL',
                  style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _urlController,
                  style: const TextStyle(color: AppTheme.textPrimary),
                  decoration: InputDecoration(
                    hintText: 'https://your-app.onrender.com',
                    hintStyle: const TextStyle(color: AppTheme.textSecondary),
                    filled: true,
                    fillColor: AppTheme.surfaceLight,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide.none,
                    ),
                    prefixIcon: const Icon(Icons.link_rounded, color: AppTheme.primary),
                    suffixIcon: _connected
                        ? const Icon(Icons.check_circle, color: AppTheme.success)
                        : null,
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: FilledButton.icon(
                    onPressed: _testing ? null : _testConnection,
                    icon: _testing
                        ? const SizedBox(
                            width: 18, height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : const Icon(Icons.wifi_find_rounded),
                    label: Text(_testing ? 'Testing...' : 'Test Connection'),
                    style: FilledButton.styleFrom(
                      backgroundColor: AppTheme.primary,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
                if (_serverInfo != null) ...[
                  const SizedBox(height: 12),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: (_connected ? AppTheme.success : AppTheme.error).withAlpha(10),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: (_connected ? AppTheme.success : AppTheme.error).withAlpha(40),
                      ),
                    ),
                    child: Text(
                      _serverInfo!,
                      style: TextStyle(
                        fontSize: 12,
                        color: _connected ? AppTheme.success : AppTheme.error,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 20),

          // About
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.surfaceLighter),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.info_outline_rounded, color: AppTheme.secondary),
                    SizedBox(width: 10),
                    Text(
                      'About',
                      style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                _aboutRow('App', 'AI Job Agent v1.0.0'),
                _aboutRow('Developer', 'Ajsal PV'),
                _aboutRow('Backend', 'FastAPI on Render'),
                _aboutRow('AI Engine', 'Groq LLaMA 3.3'),
                _aboutRow('Platforms', '6 (LinkedIn, Indeed, Naukri, Hirist, Glassdoor, Wellfound)'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _aboutRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          SizedBox(
            width: 90,
            child: Text(label, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13)),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }
}
