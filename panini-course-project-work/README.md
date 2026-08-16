# Synced Colab Work Outputs

This directory is the Git-tracked snapshot destination for the durable Colab work root:

```text
/content/drive/MyDrive/panini-course-project-work
```

Use the sync helper from the repository root after mounting Google Drive in Colab:

```bash
python tools/sync_colab_work.py --source /content/drive/MyDrive/panini-course-project-work --dest panini-course-project-work
```

To commit and push from an authenticated clone:

```bash
python tools/sync_colab_work.py --source /content/drive/MyDrive/panini-course-project-work --dest panini-course-project-work --commit --push
```

The script copies JSONL checkpoints safely by dropping an incomplete trailing JSONL row if a long-running notebook cell is appending at the same time. The source Drive files are never modified.
