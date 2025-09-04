// const common_site_config = require('../../../sites/common_site_config.json');
// const { webserver_port } = common_site_config;

export default {
	"^/(app|api|assets|files|private)": {
		target: `https://uat.walnutedu.in`,
		changeOrigin: true,
	},
};
