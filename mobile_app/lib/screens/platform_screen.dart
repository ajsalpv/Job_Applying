import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import 'job_detail_screen.dart';

class PlatformScreen extends StatefulWidget {
  final String platform;
  const PlatformScreen({super.key, required this.platform});

  @override
  State<PlatformScreen> createState() => _PlatformScreenState();
}

class _PlatformScreenState extends State<PlatformScreen> {
  List<dynamic> _jobs = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadJobs();
  }

  Future<void> _loadJobs() async {
    setState(() { _loading = true; _error = null; });
    try {
      final data = await ApiService.getJobsByPlatform(widget.platform);
      setState(() {
        _jobs = data['jobs'] ?? [];
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
    final color = AppTheme.platformColor(widget.platform);
    final icon = AppTheme.platformIcon(widget.platform);
    final name = widget.platform[0].toUpperCase() + widget.platform.substring(1);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Text(icon, style: const TextStyle(fontSize: 24)),
            const SizedBox(width: 8),
            Text(name),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _loadJobs,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
          : _error != null
              ? _buildError()
              : RefreshIndicator(
                  onRefresh: _loadJobs,
                  color: color,
                  child: _jobs.isEmpty ? _buildEmpty(name) : _buildJobList(color),
                ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 50, color: AppTheme.error),
          const SizedBox(height: 16),
          Text('Failed to load jobs', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          Text(_error ?? '', style: Theme.of(context).textTheme.bodyMedium, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          FilledButton.icon(onPressed: _loadJobs, icon: const Icon(Icons.refresh), label: const Text('Retry')),
        ],
      ),
    );
  }

  Widget _buildEmpty(String name) {
    return ListView(
      children: [
        SizedBox(
          height: MediaQuery.of(context).size.height * 0.6,
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(AppTheme.platformIcon(widget.platform), style: const TextStyle(fontSize: 64)),
                const SizedBox(height: 16),
                Text('No jobs from $name yet', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                Text(
                  'Jobs will appear here after the agent\ncompletes a scan on $name',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildJobList(Color color) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _jobs.length + 1, // +1 for header
      itemBuilder: (context, index) {
        if (index == 0) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(
                    color: color.withAlpha(25),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: color.withAlpha(60)),
                  ),
                  child: Text(
                    '${_jobs.length} jobs',
                    style: TextStyle(color: color, fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
          );
        }

        final job = _jobs[index - 1];
        return _JobCard(
          job: job,
          color: color,
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => JobDetailScreen(job: job),
              ),
            );
          },
          onOpenLink: () async {
            final url = job['job_url'] ?? '';
            if (url.isNotEmpty) {
              await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
            }
          },
        );
      },
    );
  }
}

class _JobCard extends StatelessWidget {
  final dynamic job;
  final Color color;
  final VoidCallback onTap;
  final VoidCallback onOpenLink;

  const _JobCard({
    required this.job,
    required this.color,
    required this.onTap,
    required this.onOpenLink,
  });

  @override
  Widget build(BuildContext context) {
    final score = job['fit_score'] ?? 0;
    final scoreColor = score >= 80 ? AppTheme.success
        : score >= 60 ? AppTheme.warning
        : AppTheme.error;
    final statusColor = _statusColor(job['status'] ?? '');

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.surfaceLighter),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Title row
              Row(
                children: [
                  Expanded(
                    child: Text(
                      job['role'] ?? 'Unknown Role',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: AppTheme.textPrimary,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Fit Score Badge
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: scoreColor.withAlpha(25),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: scoreColor.withAlpha(80)),
                    ),
                    child: Text(
                      '$score%',
                      style: TextStyle(
                        color: scoreColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              // Company and location
              Row(
                children: [
                  const Icon(Icons.business_rounded, size: 14, color: AppTheme.textSecondary),
                  const SizedBox(width: 5),
                  Expanded(
                    child: Text(
                      job['company'] ?? '',
                      style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Row(
                children: [
                  const Icon(Icons.location_on_rounded, size: 14, color: AppTheme.textSecondary),
                  const SizedBox(width: 5),
                  Expanded(
                    child: Text(
                      job['location'] ?? '',
                      style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Bottom row: Status + Open Link
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusColor.withAlpha(20),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      job['status'] ?? 'unknown',
                      style: TextStyle(color: statusColor, fontSize: 12, fontWeight: FontWeight.w600),
                    ),
                  ),
                  const Spacer(),
                  TextButton.icon(
                    onPressed: onTap,
                    icon: const Icon(Icons.school_rounded, size: 16),
                    label: const Text('Prep', style: TextStyle(fontSize: 12)),
                    style: TextButton.styleFrom(
                      foregroundColor: AppTheme.secondary,
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                    ),
                  ),
                  TextButton.icon(
                    onPressed: onOpenLink,
                    icon: const Icon(Icons.open_in_new_rounded, size: 16),
                    label: const Text('Open', style: TextStyle(fontSize: 12)),
                    style: TextButton.styleFrom(
                      foregroundColor: color,
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'applied': return AppTheme.primary;
      case 'interview': return AppTheme.success;
      case 'offer': return AppTheme.warning;
      case 'rejected': return AppTheme.error;
      default: return AppTheme.textSecondary;
    }
  }
}
