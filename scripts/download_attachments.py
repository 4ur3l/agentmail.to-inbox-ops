import os
from pathlib import Path

import httpx

from common import build_parser, emit, get_client_and_inbox, log_action


def main() -> None:
    p = build_parser("Download message attachments")
    p.add_argument("message_id")
    p.add_argument("--out-dir", default="./downloads")
    p.add_argument("--attachment-id", default=None)
    args = p.parse_args()

    client, inbox = get_client_and_inbox(args)
    log_action("download_attachments.start", inbox=inbox, message_id=args.message_id, out_dir=args.out_dir, attachment_id=args.attachment_id)
    msg = client.inboxes.messages.get(inbox_id=inbox, message_id=args.message_id)
    attachments = msg.attachments or []

    if args.attachment_id:
        attachments = [a for a in attachments if a.attachment_id == args.attachment_id]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for a in attachments:
        meta = client.inboxes.messages.get_attachment(
            inbox_id=inbox, message_id=args.message_id, attachment_id=a.attachment_id
        )
        filename = a.filename or f"{a.attachment_id}.bin"
        target = out_dir / filename

        r = httpx.get(meta.download_url, timeout=60.0)
        r.raise_for_status()
        target.write_bytes(r.content)

        downloaded.append(
            {
                "attachment_id": a.attachment_id,
                "filename": filename,
                "path": str(target.resolve()),
                "bytes": len(r.content),
                "content_type": a.content_type,
            }
        )

    log_action("download_attachments.done", inbox=inbox, message_id=args.message_id, downloaded_count=len(downloaded))
    emit({"inbox": inbox, "message_id": args.message_id, "downloaded": downloaded})


if __name__ == "__main__":
    main()
