import ami_tools


def extract_core_info(msg):
    output = msg.Output
    result = {}
    keys = ["Version:", "System:", "Entity ID:", "PBX UUID:"]
    key_map = {
        "Version:": "version",
        "System:": "system",
        "Entity ID:": "entity_id",
        "PBX UUID:": "pbx_uuid",
    }
    for line in output:
        line = line.strip()
        for k in keys:
            if line.startswith(k):
                result[key_map[k]] = line.split(":", 1)[1].strip()
    return result


async def collect_core_info():
    resp = await ami_tools.run_action({"Action": "Command", "Command": "core show settings"})
    contexts_dict = await ami_tools.update_all_peers()
    info = extract_core_info(resp)
    info["contexts"] = [{"context": c, "endpoint": e} for c, e in contexts_dict.items()]
    return info
