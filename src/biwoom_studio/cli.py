import argparse
import json
from .core import create_fixture, approve_fixture_only, preview, layout

def main():
    parser = argparse.ArgumentParser(description='Local mock demo or P1 draft validation; no live mode or approval')
    parser.add_argument('command', choices=['demo','validate','p2-demo','preflight','status','p3-start','p3-resume','raster-demo','p4-demo','korean-demo','pipeline-demo'])
    parser.add_argument('story_id', nargs='?')
    args = parser.parse_args()
    if args.command == 'pipeline-demo':
        if args.story_id: parser.error('synthetic pipeline only')
        from .audit.pipeline import demo as pipeline_demo
        print(json.dumps(pipeline_demo(),indent=2)); return 0
    if args.command == 'korean-demo':
        if args.story_id: parser.error('synthetic only')
        from .composition.korean import demo as korean_demo
        print(json.dumps(korean_demo(),indent=2)); return 0
    if args.command == 'p4-demo':
        if args.story_id: parser.error('p4-demo accepts no story: synthetic only')
        from .composition.vertical import demo as p4_demo
        print(json.dumps(p4_demo(),indent=2)); return 0
    if args.command == 'raster-demo':
        if args.story_id: parser.error('raster-demo accepts no story: fixture only')
        from .qa.raster import demo as raster_demo
        print(json.dumps(raster_demo(),indent=2)); return 0
    if args.command in ('p3-start','p3-resume'):
        from .qa.offline import start, resume
        try:
            if args.command == 'p3-start':
                if args.story_id: parser.error('p3-start accepts no story: synthetic fixture only')
                result = {'run_name':start(),'phase':'paused','mock_only':True}
            else:
                if not args.story_id: parser.error('p3-resume requires run_name')
                result = resume(args.story_id)
        except (ValueError,OSError,KeyError,TypeError) as exc:
            print(json.dumps({'error':str(exc),'mock_only':True})); return 1
        print(json.dumps(result,indent=2)); return 2 if result['phase']=='stalled' else 0
    if args.command in ('preflight','status'):
        if not args.story_id: parser.error('preflight/status requires ST-NNN')
        from .audit.preflight import preflight
        try:
            result = preflight(args.story_id)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            print(json.dumps({'read_only':True,'error':str(exc),'live_allowed':False,'release_allowed':False}))
            return 1
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 2 if result['blockers'] else 0
    if args.command == 'p2-demo':
        if not args.story_id: parser.error('p2-demo requires ST-NNN')
        from .generation.mock import demo as p2_demo
        try:
            result = p2_demo(args.story_id)
        except (ValueError, OSError, RuntimeError, StopIteration) as exc:
            print(json.dumps({'error':str(exc),'mock_only':True}))
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == 'validate':
        if not args.story_id: parser.error('validate requires ST-NNN')
        from .models.p1 import validate_story
        try:
            result = validate_story(args.story_id)
        except (ValueError, OSError) as exc:
            print(json.dumps({'schema_valid':False,'errors':[type(exc).__name__ + ': ' + str(exc)]}))
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return not result['schema_valid']
    if args.story_id: parser.error('demo accepts no story input')
    run = create_fixture()
    preview(run)  # Deliberately demonstrates a clearly labelled unapproved preview.
    approve_fixture_only(run)
    errors = layout(run)
    print(json.dumps({'mock_only':True, 'run':str(run), 'errors':errors}, indent=2))
    return bool(errors)

if __name__ == '__main__':
    raise SystemExit(main())
