import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';

class EmailLogsScreen extends StatefulWidget {
  const EmailLogsScreen({super.key});

  @override
  State<EmailLogsScreen> createState() => _EmailLogsScreenState();
}

class _EmailLogsScreenState extends State<EmailLogsScreen> {
  List<dynamic> _logs = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadLogs();
  }

  Future<void> _loadLogs() async {
    setState(() { _loading = true; _error = null; });
    try {
      final logs = await ApiService.getEmailLogs();
      setState(() {
        _logs = logs;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Email History'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _loadLogs,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
          : _error != null
              ? _buildError()
              : _logs.isEmpty
                  ? _buildEmpty()
                  : _buildLogList(),
    );
  }

  Widget _buildLogList() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _logs.length,
      itemBuilder: (context, index) {
        final log = _logs[index];
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.surfaceLighter),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 40, height: 40,
                decoration: BoxDecoration(
                  color: AppTheme.primary.withAlpha(30),
                  shape: BoxShape.circle,
                ),
                child: const Center(
                  child: Icon(Icons.email_outlined, color: AppTheme.primary, size: 20),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      log['job_name'] ?? 'Unknown Job',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'To: ${log['recipient'] ?? ''}',
                      style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.calendar_today_rounded, size: 12, color: AppTheme.textSecondary),
                        const SizedBox(width: 4),
                        Text(log['date'] ?? '', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                        const SizedBox(width: 16),
                        const Icon(Icons.access_time_rounded, size: 12, color: AppTheme.textSecondary),
                        const SizedBox(width: 4),
                        Text(log['time'] ?? '', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.mail_outline_rounded, size: 64, color: AppTheme.textSecondary),
          const SizedBox(height: 16),
          const Text('No emails sent yet', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          const Text('Apply to jobs to see your history here.', style: TextStyle(color: AppTheme.textSecondary)),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline_rounded, size: 50, color: AppTheme.error),
          const SizedBox(height: 16),
          const Text('Failed to load logs'),
          const SizedBox(height: 16),
          FilledButton(onPressed: _loadLogs, child: const Text('Retry')),
        ],
      ),
    );
  }
}
