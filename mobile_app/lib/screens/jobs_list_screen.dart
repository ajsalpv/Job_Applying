import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import 'job_detail_screen.dart';

enum JobsListMode { discovered, applied }

class JobsListScreen extends StatefulWidget {
  final JobsListMode mode;
  const JobsListScreen({super.key, required this.mode});

  @override
  State<JobsListScreen> createState() => _JobsListScreenState();
}

class _JobsListScreenState extends State<JobsListScreen> {
  List<dynamic> _jobs = [];
  bool _loading = true;
  String? _error;
  String _selectedPlatform = 'All';

  final List<String> _platforms = ['All', 'linkedin', 'indeed', 'naukri', 'wellfound', 'hirist', 'glassdoor'];

  @override
  void initState() {
    super.initState();
    _loadJobs();
  }

  Future<void> _loadJobs() async {
    if (!mounted) return;
    setState(() { _loading = true; _error = null; });
    try {
      final allApps = await ApiService.getAllApplications();
      
      setState(() {
        if (widget.mode == JobsListMode.discovered) {
          _jobs = allApps.where((app) => app['status'].toString().toLowerCase() == 'discovered').toList();
        } else {
          _jobs = allApps.where((app) => ['applied', 'interview', 'offer', 'rejected'].contains(app['status'].toString().toLowerCase())).toList();
          // Sort applied jobs by applied_at if available, otherwise by date
          _jobs.sort((a, b) {
            final aTime = a['applied_at']?.toString() ?? a['date']?.toString() ?? '';
            final bTime = b['applied_at']?.toString() ?? b['date']?.toString() ?? '';
            return bTime.compareTo(aTime);
          });
        }
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  List<dynamic> get _filteredJobs {
    if (_selectedPlatform == 'All') return _jobs;
    return _jobs.where((job) => job['platform'].toString().toLowerCase() == _selectedPlatform.toLowerCase()).toList();
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.mode == JobsListMode.discovered ? 'Discovery' : 'Applications';
    final primaryColor = widget.mode == JobsListMode.discovered ? AppTheme.secondary : AppTheme.primary;

    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _loadJobs,
          ),
        ],
      ),
      body: Column(
        children: [
          _buildPlatformFilter(),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
                : _error != null
                    ? _buildError()
                    : RefreshIndicator(
                        onRefresh: _loadJobs,
                        color: AppTheme.primary,
                        child: _filteredJobs.isEmpty 
                            ? _buildEmpty() 
                            : _buildJobList(primaryColor),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildPlatformFilter() {
    return Container(
      height: 50,
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: _platforms.length,
        itemBuilder: (context, index) {
          final p = _platforms[index];
          final isSelected = _selectedPlatform == p;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              selected: isSelected,
              label: Text(p == 'All' ? 'All' : p[0].toUpperCase() + p.substring(1)),
              onSelected: (val) => setState(() => _selectedPlatform = p),
              selectedColor: AppTheme.primary.withAlpha(50),
              labelStyle: TextStyle(
                color: isSelected ? AppTheme.primary : AppTheme.textSecondary,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              ),
              backgroundColor: AppTheme.surface,
              side: BorderSide(color: isSelected ? AppTheme.primary : AppTheme.surfaceLighter),
            ),
          );
        },
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
          const Text('Failed to load jobs', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text(_error ?? '', textAlign: TextAlign.center, style: const TextStyle(color: AppTheme.textSecondary)),
          const SizedBox(height: 16),
          FilledButton.icon(onPressed: _loadJobs, icon: const Icon(Icons.refresh), label: const Text('Retry')),
        ],
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            widget.mode == JobsListMode.discovered ? Icons.search_off_rounded : Icons.send_and_archive_rounded,
            size: 64, color: AppTheme.textSecondary
          ),
          const SizedBox(height: 16),
          Text(
            widget.mode == JobsListMode.discovered 
                ? 'No new jobs discovered' 
                : 'No applied jobs yet',
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)
          ),
          const SizedBox(height: 8),
          const Text(
            'Keep exploring to find your dream job! 🚀',
            style: TextStyle(color: AppTheme.textSecondary)
          ),
        ],
      ),
    );
  }

  Widget _buildJobList(Color color) {
    final jobs = _filteredJobs;
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: jobs.length,
      itemBuilder: (context, index) {
        final job = jobs[index];
        return JobItemCard(
          job: job,
          onTap: () async {
            final result = await Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => JobDetailScreen(job: job),
              ),
            );
            if (result == true) _loadJobs();
          },
        );
      },
    );
  }
}

class JobItemCard extends StatelessWidget {
  final dynamic job;
  final VoidCallback onTap;

  const JobItemCard({super.key, required this.job, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final score = job['fit_score'] ?? 0;
    final scoreColor = score >= 80 ? AppTheme.success
        : score >= 60 ? AppTheme.warning
        : AppTheme.error;
    
    final platform = job['platform']?.toString() ?? 'unknown';
    final platformColor = AppTheme.platformColor(platform);

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
              Row(
                children: [
                  Container(
                    width: 32, height: 32,
                    decoration: BoxDecoration(
                      color: platformColor.withAlpha(30),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Center(
                      child: Text(AppTheme.platformIcon(platform), style: const TextStyle(fontSize: 18)),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          job['role'] ?? 'Unknown Role',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                          maxLines: 1, overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          job['company'] ?? 'Unknown Company',
                          style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                          maxLines: 1, overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: scoreColor.withAlpha(25),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: scoreColor.withAlpha(60)),
                    ),
                    child: Text(
                      '$score%',
                      style: TextStyle(color: scoreColor, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  const Icon(Icons.location_on_outlined, size: 14, color: AppTheme.textSecondary),
                  const SizedBox(width: 4),
                  Text(job['location'] ?? '', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                  const Spacer(),
                  Text(
                    job['applied_at'] != null && job['applied_at'].toString().isNotEmpty
                      ? 'Applied: ${job['applied_at'].toString().split(' ')[0]}'
                      : 'Found: ${job['date']}',
                    style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
