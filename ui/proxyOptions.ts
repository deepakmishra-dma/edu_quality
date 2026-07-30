import fs from "fs";
import path from "path";

const DEFAULT_WEBSERVER_PORT = 8000;

/**
 * Port the bench's web server is listening on.
 *
 * `sites/common_site_config.json` belongs to the bench, not to this repo, so it
 * is read at runtime rather than `require`d. A static require makes the file a
 * build-time dependency of the Vite config, which breaks `vite build` in any
 * clean checkout (CI included). Missing file simply falls back to the default.
 */
function getWebserverPort(): number {
  const configPath = path.resolve(
    process.cwd(),
    "../../../sites/common_site_config.json"
  );

  try {
    const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
    return Number(config.webserver_port) || DEFAULT_WEBSERVER_PORT;
  } catch {
    return DEFAULT_WEBSERVER_PORT;
  }
}

const webserver_port = getWebserverPort();

export default {
  "^/(app|api|assets|files|private)": {
    target: `http://127.0.0.1:${webserver_port}`,
    // ws: true,
    // changeOrigin: true,
    router: function (req: any) {
      const site_name = req.headers.host.split(":")[0];
      return `http://${site_name}:${webserver_port}`;
    },
  },
};
